"""
VIKRAM AI - Text-to-Speech Engine
Uses Windows native Speech Synthesis (SAPI5 / System.Speech) to produce a calm,
authoritative, medium-low futuristic voice addressing the user as 'Master'.
"""

import logging
import os
import queue
import re
import subprocess
import threading
from collections.abc import Callable

from ..database.sqlite import db

from .neural_tts import is_telugu, neural_tts

logger = logging.getLogger("vikram.assistant.tts")



class TextToSpeechEngine:
    def __init__(self):
        self.speech_queue: queue.Queue = queue.Queue()
        self.is_speaking: bool = False
        self.is_paused: bool = False
        self.last_spoken_time: float = 0.0
        self.last_spoken_text: str = ""
        self._worker_thread: threading.Thread | None = None
        self._running: bool = True
        self.on_speak_start: Callable[[str], None] | None = None
        self.on_speak_end: Callable[[str], None] | None = None
        self._start_worker()

    def _start_worker(self):
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True, name="VikramTTSWorker")
        self._worker_thread.start()

    def _process_queue(self):
        import time
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception as e:
            logger.debug(f"pythoncom CoInitialize notice: {e}")

        sp_voice = None
        try:
            import win32com.client
            sp_voice = win32com.client.Dispatch("SAPI.SpVoice")
            logger.info("Native Windows SAPI.SpVoice COM synthesizer ready as fallback.")
        except Exception as e:
            logger.warning(f"Native win32com SAPI not available, fallback to PowerShell: {e}")

        while self._running:
            try:
                item = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not item or self.is_paused:
                self.speech_queue.task_done()
                continue

            if isinstance(item, tuple):
                text, lang = item
            else:
                text = str(item)
                lang = "te" if is_telugu(text) else "en"

            if not text.strip():
                self.speech_queue.task_done()
                continue

            self.is_speaking = True
            self.speak_start_time = time.time()
            self.last_spoken_text = text
            if self.on_speak_start:
                try:
                    self.on_speak_start(text)
                except Exception as e:
                    logger.error(f"Error in on_speak_start callback: {e}")

            try:
                # Prioritize human-like neural TTS for both Telugu and English
                neural_ok = False
                try:
                    neural_ok = neural_tts.speak(text, lang=lang, block=True)
                except Exception as e:
                    logger.warning(f"Neural TTS playback error: {e}")

                if not neural_ok:
                    # Fallback to local Windows SAPI
                    try:
                        if sp_voice:
                            self._speak_native_sapi(sp_voice, text)
                        else:
                            self._speak_windows(text)
                    except Exception as e:
                        logger.error(f"Fallback TTS error: {e}")
                        try:
                            self._speak_windows(text)
                        except Exception as inner_e:
                            logger.error(f"PowerShell TTS failed: {inner_e}")
            finally:
                self.last_spoken_time = time.time()
                self.is_speaking = False
                if self.on_speak_end:
                    try:
                        self.on_speak_end(text)
                    except Exception as e:
                        logger.error(f"Error in on_speak_end callback: {e}")
                self.speech_queue.task_done()


    def _find_male_sapi_voice(self, sp_voice):
        """Finds and returns a guaranteed Male SAPI voice on any Windows system."""
        male_keywords = [
            "andrew", "brian", "davis", "roger", "guy", "ravi", "david", "mark",
            "george", "prabhat", "mohan", "richard", "james", "male", "sean", "cosmo",
            "paul", "steven", "daniel", "charles", "frank", "alex"
        ]
        female_keywords = [
            "heera", "zira", "hazel", "eva", "female", "susan", "catherine", "linda",
            "veena", "kalpana", "harita", "jenny", "aria", "sonia", "neerja", "shruti",
            "chitra", "swara", "geeta", "ananya", "priya", "sunita", "cortana", "girl",
            "woman", "child", "christopher", "mary", "sarah", "karen", "samantha",
            "victoria", "ayanda"
        ]

        try:
            voices = list(sp_voice.GetVoices())
        except Exception:
            return None

        # 1. Match known male keyword
        for v in voices:
            desc = v.GetDescription().lower()
            if any(mk in desc for mk in male_keywords) and not any(fk in desc for fk in female_keywords):
                logger.info(f"Selected native Windows male voice: {v.GetDescription()}")
                return v

        # 2. Try SAPI Category Gender=Male query
        try:
            cat = sp_voice.GetVoices("Gender=Male")
            if cat and cat.Count > 0:
                for i in range(cat.Count):
                    item = cat.Item(i)
                    desc = item.GetDescription().lower()
                    if not any(fk in desc for fk in female_keywords):
                        logger.info(f"Selected native Windows male voice by category: {item.GetDescription()}")
                        return item
        except Exception:
            pass

        # Zero tolerance for female voices: NEVER fallback to an unverified voice
        logger.warning("No confirmed male SAPI voice found. Refusing to use unverified voice.")
        return None

    def _speak_native_sapi(self, sp_voice, text: str):
        """Ultra-low-latency native Windows SAPI COM synthesis with strict MALE voice enforcement."""
        clean_text = re.sub(r"```[\s\S]*?```", "", text)
        clean_text = re.sub(r"`[^`]*`", "", clean_text)
        clean_text = re.sub(r"[\*#_~\[\]\(\)]", "", clean_text).strip()

        # Strictly select male voice
        male_voice = self._find_male_sapi_voice(sp_voice)
        if not male_voice:
            # Under NO circumstance allow SAPI to use default female voice!
            logger.warning("No male SAPI voice found, routing to deep male PowerShell synthesis.")
            self._speak_windows(text)
            return

        sp_voice.Voice = male_voice

        # Set voice parameters (slightly lower rate gives deeper, more authoritative cadence)
        volume = int(db.get_setting("voice_volume", "100") or "100")
        rate = int(db.get_setting("voice_speed", "-2") or "-2")
        sp_voice.Volume = max(0, min(100, volume))
        sp_voice.Rate = max(-10, min(10, rate))

        try:
            sp_voice.Speak(clean_text, 0)
        except Exception:
            self._speak_windows(clean_text)

    def _speak_windows(self, text: str):
        """Fallback: Invokes PowerShell System.Speech synthesizer with strict MALE filter."""
        rate = int(db.get_setting("voice_speed", "-2") or "-2")
        volume = int(db.get_setting("voice_volume", "100") or "100")

        clean_text = text.replace("'", "''").replace('"', " ")

        ps_script = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Volume = {volume}; "
            f"$synth.Rate = {rate}; "
            f"$maleVoice = $synth.GetInstalledVoices() | Where-Object {{ "
            f"    $_.Enabled -and ( "
            f"        $_.VoiceInfo.Gender -eq [System.Speech.Synthesis.VoiceGender]::Male -or "
            f"        $_.VoiceInfo.Name -match 'Ravi|David|Mark|George|Prabhat|Male|Guy|Andrew|Brian' "
            f"    ) -and ( "
            f"        $_.VoiceInfo.Name -notmatch 'Heera|Zira|Hazel|Eva|Female|Veena|Kalpana|Harita|Jenny|Aria|Sonia|Neerja|Shruti|Chitra|Swara|Geeta|Ananya|Priya|Sunita|Cortana|Christopher' "
            f"    ) "
            f"}} | Select-Object -First 1; "
            f"if ($maleVoice) {{ "
            f"    $synth.SelectVoice($maleVoice.VoiceInfo.Name); "
            f"    $synth.Speak('{clean_text}'); "
            f"}}"
        )

        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )

    def speak(self, text: str, lang: str = "auto", priority: bool = False):
        """Queues a message to be spoken in human-like neural voice."""
        if not text:
            return

        target_lang = "te" if (lang == "te" or (lang == "auto" and is_telugu(text))) else "en"

        # Ensure worker is alive and not paused
        self._running = True
        self.is_paused = False
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._start_worker()

        if priority:
            with self.speech_queue.mutex:
                self.speech_queue.queue.clear()
        self.speech_queue.put((text, target_lang))

    def speak_multilingual(self, text: str, lang_code: str = "en"):
        """Speaks text in Telugu or English using human-like neural voice."""
        self.speak(text, lang=lang_code)

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._running = True
            self._start_worker()

    def interrupt(self):
        """Immediately halts active speech and clears queued audio."""
        self.is_speaking = False
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
        try:
            import ctypes
            ctypes.windll.winmm.mciSendStringW('close all', None, 0, None)
        except Exception:
            pass

    def stop(self):
        """Halts current speech and clears queue without killing the background worker thread."""
        self.interrupt()

    def shutdown(self):
        """Kills worker thread on complete application termination."""
        self._running = False
        self.interrupt()



# Global TTS instance
tts = TextToSpeechEngine()
