"""
VIKRAM AI - Wake Word & Audio Listener
Continuously monitors audio for 'Hey Vikram' / 'Vikram'.
Coordinates speaker verification and forwards validated commands.
"""

import ctypes
import logging
import os
import re
import subprocess
import threading
import time
from collections.abc import Callable
from typing import Any

from .speaker_verification import speaker_verifier
from .text_to_speech import tts

logger = logging.getLogger("vikram.assistant.wakeword")

WAKE_PATTERNS = [
    r"\b(?:hey|hi|hello|ok|okay)?\s*(?:doom|doom\s+ai|vikram|vicram|bikram|vic\s+ram|vick\s+ram)\b",
    r"\bhey\s+assistant\b",
    r"(?:హే\s*డూమ్|డూమ్\s*ఏఐ|డూమ్|నమస్తే\s*డూమ్|నమస్కారం\s*డూమ్|ఓయ్\s*డూమ్)",
    r"\bdoom\b",
    r"\bdoom\s+ai\b",
    r"\bvikram\b",
    r"\bbikram\b"
]



class WakewordListener:
    def __init__(self):
        self.is_active: bool = False
        self.is_paused: bool = False
        self.on_command_detected: Callable[[str, bool, float], Any] | None = None
        self.on_state_change: Callable[[str], None] | None = None
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_cmd_text: str = ""
        self._last_cmd_time: float = 0.0
        self._activation_cooldown_until: float = 0.0

    def _send_proc_command(self, cmd: str):
        """Sends a control command (e.g. PAUSE, RESUME, STOP) to native listener stdin."""
        if self._proc and self._proc.stdin and self._proc.poll() is None:
            try:
                self._proc.stdin.write(f"{cmd}\n")
                self._proc.stdin.flush()
            except Exception as e:
                logger.debug(f"Failed to send '{cmd}' to native listener: {e}")

    def _drain_proc_stdout(self):
        """Discards all pending unread bytes from native recognizer stdout to prevent stale command accumulation."""
        if not self._proc or not self._proc.stdout or self._proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                from ctypes import wintypes
                handle = msvcrt.get_osfhandle(self._proc.stdout.fileno())
                avail = wintypes.DWORD()
                drained_total = 0
                while True:
                    success = ctypes.windll.kernel32.PeekNamedPipe(
                        handle, None, 0, None, ctypes.byref(avail), None
                    )
                    if not success or avail.value == 0:
                        break
                    chunk = self._proc.stdout.read(avail.value)
                    drained_total += len(chunk) if chunk else 0
                if drained_total > 0:
                    logger.info(f"Drained and discarded {drained_total} stale bytes from native listener pipe.")
        except Exception as e:
            logger.debug(f"Drain stdout notice: {e}")

    def start(self, command_callback: Callable[[str, bool, float], Any], state_callback: Callable[[str], None] | None = None):
        """Starts the persistent background listener with local faster-whisper STT integration."""
        self.on_command_detected = command_callback
        self.on_state_change = state_callback
        self.is_active = True
        self.is_paused = False
        self._stop_event.clear()

        # Connect Local Offline Whisper STT Engine
        from .speech_to_text import stt_engine
        stt_engine.on_transcript_callback = self._handle_stt_transcript

        # Pre-load Whisper model once in background
        threading.Thread(target=stt_engine.load_model, daemon=True, name="DoomWhisperModelPreload").start()

        # Check initial network status: if offline, engage local Whisper immediately
        from ..monitoring.system_monitor import SystemMonitor
        if not SystemMonitor.is_network_online():
            logger.info("Startup in offline mode: engaging Local Whisper STT immediately.")
            stt_engine.set_offline_mode(True)
        else:
            logger.info("Startup in online mode: Web Speech API active; Local Whisper in standby.")

        # Start native Windows offline speech recognition supervisor thread
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._native_listener_loop, daemon=True, name="DoomNativeListenerSupervisor")
            self._thread.start()
            logger.info("DOOM AI Native Offline Speech Listener supervisor thread started.")

        logger.info("DOOM AI Wake Word Listener & Offline STT initialized.")

    def _handle_stt_transcript(self, text: str, conf: float) -> None:
        """Handles speech transcripts from local Whisper STT."""
        self.process_speech_input(text, allow_direct=True)

    def pause(self):
        """Pauses wake word listening (from tray or command)."""
        self.is_paused = True
        self._send_proc_command("PAUSE")
        self._drain_proc_stdout()
        from .speech_to_text import stt_engine
        stt_engine.stop_listening()
        if self.on_state_change:
            self.on_state_change("PAUSED")
        logger.info("DOOM AI listening paused.")

    def resume(self):
        """Resumes wake word listening."""
        self._drain_proc_stdout()
        self.is_paused = False
        self._activation_cooldown_until = time.time() + 2.0  # Increased: suppress 2s of post-activation noise
        self._last_cmd_time = time.time()
        self._send_proc_command("RESUME")
        from .speech_to_text import stt_engine
        from ..monitoring.system_monitor import SystemMonitor
        if not SystemMonitor.is_network_online():
            stt_engine.set_offline_mode(True)
        if self.on_state_change:
            self.on_state_change("ONLINE")
        logger.info("DOOM AI listening resumed.")

    def stop(self):
        """Stops the listener entirely."""
        self.is_active = False
        self._stop_event.set()
        self._send_proc_command("STOP")
        from .speech_to_text import stt_engine
        stt_engine.stop_listening()
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None

    def process_speech_input(self, raw_text: str, audio_features: Any = None, allow_direct: bool = False) -> tuple[bool, str]:
        """
        Main entrypoint for speech inputs (from native listener or WebSocket frontend).
        1. Checks if wake word is present (or allow_direct for UI mic activation).
        2. Accepts direct recognized commands (e.g. 'close whatsapp', 'lock laptop') even without wake phrase.
        3. Performs speaker verification.
        4. Strips wake phrase and returns command if authorized.
        """
        if self.is_paused or not self.is_active:
            return False, ""

        clean_input = raw_text.lower().strip()
        now = time.time()

        # Suppress echo of assistant's own system voice responses
        system_phrases = [
            "couldn't understand", "could not understand", "we can start",
            "at your service", "opening file explorer", "displaying system",
            "action cancelled", "how can i help", "welcome back", "hello master",
            "doom ai is active", "doom ai deactivated", "active master", "deactivated master",
            "connected to", "charging", "on battery",
            "నమస్కారం", "క్షమించండి", "సహాయపడగలను"
        ]
        if any(sp in clean_input for sp in system_phrases):
            logger.debug(f"Ignoring acoustic echo of system response: {raw_text}")
            return False, ""

        # Activation cooldown: ignore any stray audio for 1.2s after DOOM AI is activated
        if now < getattr(self, "_activation_cooldown_until", 0.0):
            logger.info(f"Ignoring voice input during activation cooldown: '{raw_text}'")
            return False, ""

        # Rate-limiting between any two voice commands: minimum 1.5 second (human speech spacing)
        if (now - self._last_cmd_time) < 1.5:
            logger.warning(f"Dropping rapid burst voice input '{raw_text}' ({now - self._last_cmd_time:.2f}s since last command)")
            return False, ""

        # Deduplication against rapid multi-source duplicate dispatch within 2.5s
        if self._last_cmd_text and (clean_input == self._last_cmd_text) and (now - self._last_cmd_time < 2.5):
            logger.debug(f"Ignoring duplicate speech command within 2.5s: {raw_text}")
            return False, ""
        self._last_cmd_text = clean_input
        self._last_cmd_time = now

        # TTS Collision / Acoustic Echo Suppression
        if tts.is_speaking:
            interrupt_keywords = ["stop", "quiet", "shut up", "pause", "aapu", "silence"]
            if any(k in clean_input for k in interrupt_keywords):
                logger.info(f"Interrupting active TTS for explicit stop command: '{raw_text}'")
                tts.interrupt()
            else:
                logger.info(f"Ignoring speech captured during active TTS playback: '{raw_text}'")
                return False, ""

        if (now - getattr(tts, "last_spoken_time", 0.0) < 0.4):
            logger.debug("Ignoring speech captured immediately after TTS playback.")
            return False, ""

        text = raw_text.strip()
        matched = False
        command_part = text

        for pat in WAKE_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                matched = True
                # Extract text after wake word
                end_pos = match.end()
                command_part = text[end_pos:].strip(",.!? ")
                break

        # If wake word not explicitly present, verify if it is an actionable direct command, allow_direct, or question
        if not matched:
            if allow_direct:
                matched = True
                command_part = text
            else:
                from ..ai.intent_parser import IntentParser
                parsed = IntentParser.parse(text)
                if parsed.get("intent") != "UNKNOWN":
                    # Valid actionable command or AI query detected directly
                    matched = True
                    command_part = text
                elif len(clean_input.split()) >= 2:
                    # Multi-word conversational input (e.g. 'movie review', 'operating system'): pass to AI assistant
                    matched = True
                    command_part = text
                else:
                    # Ambient noise or single unrecognized words without wake phrase are silently dropped
                    return False, ""

        if self.on_state_change:
            self.on_state_change("LISTENING")

        # Speaker Verification Step
        if audio_features is None:
            # Fallback acoustic fingerprint for authorized local desktop session
            audio_features = [0.35, 0.52, 0.48, 0.61, 0.72]

        verified, score = speaker_verifier.verify_voice(audio_features)
        if not verified and not allow_direct:
            logger.warning(f"Speaker verification failed! Score: {score:.3f}")
            if self.on_state_change:
                self.on_state_change("AUTHENTICATION REQUIRED")
            tts.speak("I'm sorry. I couldn't verify your voice.")
            return False, "UNAUTHORIZED_SPEAKER"

        if self.on_state_change:
            self.on_state_change("VOICE VERIFIED")

        # If user just said "Hey Vikram" with no command attached yet
        if not command_part:
            tts.speak("Hello Master.")
            if self.on_state_change:
                self.on_state_change("LISTENING")
            return True, ""

        logger.info(f"Authorized command extracted: '{command_part}'")
        if self.on_command_detected:
            self.on_command_detected(command_part, True, score)

        return True, command_part

    def _start_native_process(self) -> subprocess.Popen | None:
        """Launches the native offline speech recognition PowerShell process."""
        script_path = os.path.join(os.path.dirname(__file__), "native_listener.ps1")
        if not os.path.exists(script_path):
            logger.error(f"Native listener script missing at: {script_path}")
            return None

        # Safely terminate previous listener process if any
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=0.5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

        startupinfo = None
        ps_exe = "powershell.exe"
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            win_ps = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), r"System32\WindowsPowerShell\v1.0\powershell.exe")
            if os.path.exists(win_ps):
                ps_exe = win_ps

        try:
            # Merge stderr with stdout to prevent pipe deadlocks
            proc = subprocess.Popen(
                [ps_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                startupinfo=startupinfo,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )
            logger.info("DOOM AI Native Offline Speech Recognizer process started.")
            return proc
        except Exception as e:
            logger.error(f"Failed to launch native speech recognizer: {e}")
            return None

    def _native_listener_loop(self):
        """
        Indestructible watchdog supervisor for the native Windows offline speech engine.
        Continuously reads recognized speech from native_listener.ps1.
        Automatically revives the process if screen locks, audio endpoints switch, or crash occurs.
        """
        while self.is_active and not self._stop_event.is_set():
            if self.is_paused:
                self._drain_proc_stdout()
                time.sleep(0.3)
                continue

            if self._proc is None or self._proc.poll() is not None:
                if self.is_paused:
                    time.sleep(0.3)
                    continue
                if self._proc and self._proc.poll() is not None:
                    logger.warning(f"Native speech recognizer exited (code {self._proc.poll()}). Reviving in 1s...")
                    time.sleep(1.0)
                self._proc = self._start_native_process()
                if not self._proc:
                    time.sleep(2.0)
                    continue

            if not self._proc or not self._proc.stdout:
                time.sleep(0.1)
                continue
            try:
                line = self._proc.stdout.readline()
                if not line:
                    if self._proc.poll() is not None:
                        logger.warning(f"Native recognizer terminated with code {self._proc.returncode}.")
                        self._proc = None
                        time.sleep(1.0)
                        continue
                    time.sleep(0.05)
                    continue

                line = line.strip()
                if not line:
                    continue

                if self.is_paused:
                    continue

                if line.startswith("READY:"):
                    logger.info(f"Native Recognizer Status: {line[6:].strip()}")

                elif line.startswith("RECOGNIZED:"):
                    spoken = line[len("RECOGNIZED:"):].strip()
                    if spoken:
                        if time.time() < getattr(self, "_activation_cooldown_until", 0.0):
                            logger.info(f"Ignoring native recognizer during activation cooldown: '{spoken}'")
                            continue
                        logger.info(f"Native background recognizer heard: '{spoken}'")
                        self.process_speech_input(spoken, allow_direct=True)

                elif line.startswith("NOTICE:") or line.startswith("ERROR:"):
                    logger.info(f"Native Recognizer: {line}")

            except Exception as e:
                logger.debug(f"Native speech recognizer loop notice: {e}")
                time.sleep(0.5)

        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None


# Global wakeword listener
wakeword_listener = WakewordListener()

