"""
DOOM AI - Local Offline Speech-to-Text Engine
Powered by faster-whisper (CTranslate2) with GPU CUDA acceleration & CPU fallback.
Works 100% OFFLINE with zero internet, zero cloud servers, zero external API keys.
Streams microphone audio via sounddevice in short responsive chunks with pre-roll buffering.
"""

import collections
import logging
import os
import queue
import sys
import threading
import time
from collections.abc import Callable
from typing import Any

import numpy as np

logger = logging.getLogger("vikram.assistant.stt")

# Path to local Whisper models
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models", "whisper")
os.makedirs(MODEL_DIR, exist_ok=True)

# Context priming prompt to ensure Whisper accurately decodes DOOM AI desktop vocabulary
WHISPER_PROMPT = (
    "Hey Doom, Vikram, open Chrome, open WhatsApp, open Calculator, open Settings, "
    "open File Explorer, open Notepad, open VS Code, volume up, volume down, mute, "
    "unmute, brightness up, brightness down, lock laptop, close, close window, "
    "close active window, close tab, battery percentage, what time is it, "
    "what is the date today, what is the date, date today, turn on wifi, turn one wifi, "
    "turn off wifi, turn wifi, turn on bluetooth, turn one bluetooth, turn off bluetooth, turn bluetooth."
)


class SpeechToTextEngine:
    def __init__(self):
        self.is_listening: bool = False
        self.is_offline_active: bool = False
        self._model = None
        self._device: str = "cpu"
        self._compute_type: str = "int8"
        self._model_lock = threading.Lock()
        self._model_loaded: bool = False

        self._stream = None
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.on_transcript_callback: Callable[[str, float], Any] | None = None

        # Energy & VAD parameters
        self.sample_rate = 16000
        self.block_size = 1024  # 64ms chunks at 16kHz
        self.silence_threshold = 0.008  # Sensitive RMS threshold for far-field speech
        self.pause_duration = 0.45  # Seconds of silence to trigger phrase completion
        self.min_speech_duration = 0.35  # Ignore tiny clicks/pops < 350ms
        self.max_speech_duration = 6.0  # Max chunk length before forced transcription

        # Timestamp tracking for deduplication
        self._last_processed_text = ""
        self._last_processed_time = 0.0

    def _ensure_cuda_dlls(self):
        """Discovers and registers local NVIDIA CUDA / cuDNN DLL paths if available."""
        if sys.platform != "win32":
            return
        # Check Python venv site-packages for nvidia packages
        site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
        nvidia_dir = os.path.join(site_packages, "nvidia")
        if os.path.exists(nvidia_dir):
            for sub in os.listdir(nvidia_dir):
                bin_dir = os.path.join(nvidia_dir, sub, "bin")
                if os.path.isdir(bin_dir) and hasattr(os, "add_dll_directory"):
                    try:
                        os.add_dll_directory(bin_dir)
                    except Exception:
                        pass
        # Check system CUDA path
        cuda_path = os.environ.get("CUDA_PATH")
        if cuda_path and os.path.isdir(cuda_path):
            bin_dir = os.path.join(cuda_path, "bin")
            if os.path.isdir(bin_dir) and hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(bin_dir)
                except Exception:
                    pass

    def load_model(self):
        """
        Loads the local faster-whisper model once into memory and reuses it:
        - If NVIDIA CUDA GPU acceleration is available, loads 'base.en' on CUDA (float16).
        - Otherwise, loads 'tiny.en' or 'base.en' on CPU (int8) for ultra-fast ~500ms responsive inference.
        """
        with self._model_lock:
            if self._model_loaded and self._model is not None:
                return

            from faster_whisper import WhisperModel

            self._ensure_cuda_dlls()

            # Attempt 1: NVIDIA GPU CUDA acceleration (float16)
            try:
                logger.info("Attempting to load local Whisper on CUDA (float16)...")
                model = WhisperModel(
                    "base.en",
                    device="cuda",
                    compute_type="float16",
                    download_root=MODEL_DIR,
                    local_files_only=True
                )
                # Verify CUDA inference with dummy array
                dummy = np.zeros(16000, dtype=np.float32)
                list(model.transcribe(dummy, beam_size=1)[0])
                self._model = model
                self._device = "cuda"
                self._compute_type = "float16"
                self._model_loaded = True
                logger.info("DOOM AI Local Whisper initialized with NVIDIA CUDA GPU acceleration (base.en).")
                return
            except Exception as e:
                logger.warning(f"CUDA initialization failed or DLLs missing ({e}). Falling back to CPU.")

            # Attempt 2: High-speed CPU fallback with int8 quantization
            # Prefer tiny.en on CPU for ultra-low latency (~500ms) with base.en fallback
            for candidate in ["tiny.en", "base.en"]:
                try:
                    logger.info(f"Loading local Whisper '{candidate}' on CPU (int8)...")
                    model = WhisperModel(
                        candidate,
                        device="cpu",
                        compute_type="int8",
                        download_root=MODEL_DIR,
                        local_files_only=True
                    )
                    # Warm-up inference
                    dummy = np.zeros(16000, dtype=np.float32)
                    list(model.transcribe(dummy, beam_size=1)[0])
                    self._model = model
                    self._device = "cpu"
                    self._compute_type = "int8"
                    self._model_loaded = True
                    logger.info(f"DOOM AI Local Whisper initialized on CPU ({candidate}, int8).")
                    return
                except Exception as cpu_err:
                    logger.warning(f"Could not load '{candidate}' on CPU: {cpu_err}")

            logger.critical("FATAL: Could not load any local Whisper model.")

    def _audio_callback(self, indata, frames, time_info, status):
        """sounddevice streaming callback that captures raw audio frames."""
        if status:
            logger.debug(f"Audio stream status notice: {status}")
        if self.is_listening and not self._stop_event.is_set():
            # Extract mono float32 channel and push to processing queue
            self._audio_queue.put(indata[:, 0].copy())

    def _broadcast_to_hud(self, event_type: str, data: Any):
        """Safely broadcasts status or transcript updates to HUD WebSocket clients."""
        try:
            from backend.app.main import sync_broadcast
            sync_broadcast(event_type, data)
        except Exception:
            pass

    def _worker_loop(self):
        """
        Background supervisor loop:
        1. Pre-roll ring buffer retains 320ms of audio before speech onset so initial words aren't cut off.
        2. Detects pause (end of utterance) via RMS voice activity detection.
        3. Suppresses playback echo while TTS is speaking.
        4. Transcribes speech using pre-loaded local Whisper model primed with DOOM AI vocabulary.
        5. Forwards recognized text directly into DOOM AI's command pipeline.
        """
        import sounddevice as sd
        from backend.assistant.text_to_speech import tts

        speech_frames: list[np.ndarray] = []
        # Pre-roll ring buffer holds 5 blocks (~320ms) of leading audio
        pre_roll_buffer: collections.deque[np.ndarray] = collections.deque(maxlen=5)
        is_in_speech = False
        silence_start: float | None = None

        logger.info("DOOM AI Local Whisper Audio Worker loop active.")

        while self.is_listening and not self._stop_event.is_set():
            try:
                chunk = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Acoustic Echo Suppression: Ignore mic input while DOOM AI's TTS is actively speaking
            if getattr(tts, "is_speaking", False):
                if speech_frames:
                    speech_frames.clear()
                pre_roll_buffer.clear()
                is_in_speech = False
                silence_start = None
                continue

            # Calculate RMS energy for voice activity detection
            rms = float(np.sqrt(np.mean(chunk**2)))

            # Broadcast audio level to HUD visualizer
            if rms > 0.005:
                self._broadcast_to_hud("audio_level", {"level": min(1.0, rms * 8.0)})

            now = time.time()

            if rms >= self.silence_threshold:
                # User is speaking
                if not is_in_speech:
                    is_in_speech = True
                    # Prepend pre-roll buffer so leading syllables ("open", "hey") are preserved
                    speech_frames.extend(pre_roll_buffer)
                    pre_roll_buffer.clear()

                silence_start = None
                speech_frames.append(chunk)

                # Cap max speech duration to prevent buffer runaway
                total_duration = (len(speech_frames) * self.block_size) / self.sample_rate
                if total_duration >= self.max_speech_duration:
                    audio_data = np.concatenate(speech_frames)
                    speech_frames.clear()
                    is_in_speech = False
                    silence_start = None
                    self._process_speech_chunk(audio_data, total_duration)

            else:
                # Silence / background ambient noise
                if is_in_speech:
                    speech_frames.append(chunk)
                    if silence_start is None:
                        silence_start = now
                    elif now - silence_start >= self.pause_duration:
                        # User stopped speaking: phrase completed!
                        audio_data = np.concatenate(speech_frames)
                        total_duration = len(audio_data) / self.sample_rate
                        speech_frames.clear()
                        is_in_speech = False
                        silence_start = None

                        if total_duration >= self.min_speech_duration:
                            self._process_speech_chunk(audio_data, total_duration)
                else:
                    # Maintain pre-roll buffer during ambient silence
                    pre_roll_buffer.append(chunk)

    def _process_speech_chunk(self, audio_data: np.ndarray, duration: float):
        """Transcribes an accumulated speech segment using the local Whisper model."""
        if self._model is None:
            self.load_model()
            if self._model is None:
                return

        from backend.assistant.text_to_speech import tts

        try:
            t0 = time.time()
            segments, info = self._model.transcribe(
                audio_data,
                vad_filter=True,
                language="en",
                beam_size=1,
                initial_prompt=WHISPER_PROMPT
            )
            raw_text = " ".join([seg.text for seg in segments]).strip()
            elapsed_ms = (time.time() - t0) * 1000.0

            if not raw_text:
                # If user spoke for a sustained period (>0.8s) but speech could not be understood
                if duration >= 0.8:
                    logger.info(f"Unintelligible speech detected ({duration:.2f}s audio). Prompting user.")
                    tts.speak("I couldn't understand that, Master.")
                return

            # Clean transcript
            clean_text = raw_text.strip(" \t\n\r\"'.,!?")
            if not clean_text:
                return

            # Deduplication check within 1.8s
            now = time.time()
            if clean_text.lower() == self._last_processed_text.lower() and (now - self._last_processed_time < 1.8):
                return

            self._last_processed_text = clean_text
            self._last_processed_time = now

            logger.info(f"[Local Whisper STT] '{clean_text}' ({elapsed_ms:.1f}ms, device: {self._device})")

            # Broadcast recognized text to HUD transcript
            self._broadcast_to_hud("transcript", {
                "sender": "YOU",
                "text": f'"{clean_text}"'
            })

            # Pass recognized speech directly into the existing DOOM AI pipeline
            self.process_incoming_text(clean_text)

        except Exception as e:
            logger.error(f"Local Whisper transcription error: {e}")

    def start_listening(self, callback: Callable[[str, float], None] | None = None):
        """Starts background microphone audio streaming and processing."""
        import sounddevice as sd
        from backend.assistant.text_to_speech import tts

        if self.is_listening:
            return

        if callback:
            self.on_transcript_callback = callback

        # Ensure Whisper model is pre-loaded in memory
        if not self._model_loaded:
            self.load_model()

        self._stop_event.clear()

        # Open sounddevice microphone stream with safe error handling
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.block_size,
                callback=self._audio_callback
            )
            self._stream.start()
            self.is_listening = True
            logger.info(f"Local Microphone Stream active ({self.sample_rate}Hz mono float32).")
        except Exception as e:
            logger.error(f"Microphone access error: {e}")
            self.is_listening = False
            tts.speak("Microphone error, Master.")
            return

        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="DoomLocalWhisperWorker"
        )
        self._worker_thread.start()
        logger.info("Local Offline Whisper STT Engine started successfully.")

    def stop_listening(self):
        """Stops background microphone audio streaming."""
        self.is_listening = False
        self._stop_event.set()

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._worker_thread and self._worker_thread.is_alive():
            try:
                self._worker_thread.join(timeout=1.0)
            except Exception:
                pass
        # Drain audio queue to prevent residual audio processing
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except Exception:
                break

        logger.info("Local Offline Whisper STT Engine stopped.")

    def set_offline_mode(self, is_offline: bool):
        """
        Coordinates online vs offline voice systems:
        - Wi-Fi ON: Local Whisper audio stream stays in standby; Web Speech API handles voice.
        - Wi-Fi OFF: Local Whisper activates microphone capture and handles 100% offline speech.
        """
        self.is_offline_active = is_offline
        if is_offline:
            if not self.is_listening:
                logger.info("Network offline: activating Local Whisper STT on microphone.")
                self.start_listening()
                self._broadcast_to_hud("state_change", {"state": "OFFLINE (VOICE ACTIVE)"})
        else:
            if self.is_listening:
                logger.info("Network online: yielding microphone to online Web Speech API.")
                self.stop_listening()
                self._broadcast_to_hud("state_change", {"state": "ONLINE"})

    def process_incoming_text(self, text: str, confidence: float = 1.0):
        """Processes recognized text arriving from local Whisper or Web Speech API."""
        if not text:
            return
        logger.info(f"STT Transcript received: '{text}' (conf: {confidence:.2f})")

        if self.on_transcript_callback:
            self.on_transcript_callback(text, confidence)
        else:
            from backend.assistant.wakeword import wakeword_listener
            wakeword_listener.process_speech_input(text, allow_direct=True)


# Global STT instance
stt_engine = SpeechToTextEngine()
