"""

VIKRAM AI - Persistent Background Service

Independent Windows background assistant daemon.

Listens for 'Hey Doom', verifies speaker, parses intent, and executes actions.

Runs continuously regardless of whether the GUI is open or closed.

"""



import logging
import threading

from collections.abc import Callable

from typing import Any



from ..ai.intent_parser import IntentParser

from ..assistant.text_to_speech import tts

from ..assistant.wakeword import wakeword_listener

from ..ai.chat_engine import chat_engine

from ..database.sqlite import db

from ..execution.action_executor import ActionDispatcher

from ..execution.application_scanner import application_scanner

from ..monitoring.battery_monitor import battery_monitor

from ..monitoring.connectivity_monitor import connectivity_monitor

from ..monitoring.microphone_booster import mic_booster

from .lifecycle import AssistantState, lifecycle



logger = logging.getLogger("vikram.service.daemon")





class BackgroundService:

    def __init__(self):

        self.is_running: bool = False

        self.broadcast_callback: Callable[[str, Any], None] | None = None

        # Serializes command execution: only ONE command runs at a time.
        # If a new command arrives while one is executing, it is dropped (not queued).
        self._command_lock = threading.Lock()
        self._command_busy: bool = False



    def set_broadcast_callback(self, callback: Callable[[str, Any], None]):

        """Registers WebSocket broadcast callback to update GUI if connected."""

        self.broadcast_callback = callback

        battery_monitor.set_broadcast_callback(callback)

        connectivity_monitor.set_broadcast_callback(callback)

        chat_engine.set_broadcast_callback(callback)



    def broadcast(self, event_type: str, data: Any):

        if self.broadcast_callback:

            try:

                self.broadcast_callback(event_type, data)

            except Exception as e:

                logger.debug(f"Broadcast notice: {e}")



    def start(self):

        """Starts the persistent background assistant."""

        if self.is_running:

            return



        self.is_running = True

        lifecycle.set_state(AssistantState.STARTING)



        # Connect TTS state hooks to lifecycle

        tts.on_speak_start = lambda text: self._on_tts_start(text)

        tts.on_speak_end = lambda text: self._on_tts_end(text)



        # Start wakeword listener

        wakeword_listener.start(

            command_callback=self.handle_command,

            state_callback=self._on_listener_state

        )



        # Start battery & power state monitor

        battery_monitor.start()



        # Start Wi-Fi and Bluetooth connectivity monitor

        connectivity_monitor.start()



        # Start Far-Field Microphone Booster (20-Meter listening range)

        mic_booster.start_watchdog()



        # Start Full-Device Application Catalog Scanner & Controller indexing

        application_scanner.start_background_scanner()



        lifecycle.set_state(AssistantState.ONLINE)

        self.broadcast("state_change", {"state": AssistantState.ONLINE.value})

        logger.info("DOOM AI Background Service is ONLINE.")

        tts.speak("Hello Master.")



    def _on_tts_start(self, text: str):

        lifecycle.set_state(AssistantState.SPEAKING)

        self.broadcast("tts_start", {"text": text, "state": AssistantState.SPEAKING.value})



    def _on_tts_end(self, text: str):

        lifecycle.set_state(AssistantState.ONLINE)

        self.broadcast("tts_end", {"text": text, "state": AssistantState.ONLINE.value})



    def _on_listener_state(self, state_name: str):

        if hasattr(AssistantState, state_name):

            lifecycle.set_state(getattr(AssistantState, state_name))

        self.broadcast("state_change", {"state": lifecycle.state})



    def handle_command(self, raw_command: str, is_voice: bool = True, auth_score: float = 1.0) -> dict[str, Any]:

        """

        Executes a user command through the full pipeline:

        Intent Parsing -> Policy -> Action Dispatcher -> Execution -> Response.

        Commands are SERIALIZED: only one command executes at a time.

        If a new command arrives while another is executing, it is dropped immediately

        (not queued), preventing simultaneous command execution.

        """

        # Non-blocking acquire: drop the command if another is already running.
        if not self._command_lock.acquire(blocking=False):
            logger.warning(
                f"Command dropped (another command is executing): '{raw_command}'. "
                "Commands are serialized — only one runs at a time."
            )
            return {"success": False, "message": "Another command is currently executing. Please wait.", "dropped": True}

        try:
            logger.info(f"Processing command: '{raw_command}' (voice: {is_voice})")

            lifecycle.set_state(AssistantState.PROCESSING)

            self.broadcast("state_change", {"state": AssistantState.PROCESSING.value, "command": raw_command})



            # Parse Intent

            parsed = IntentParser.parse(raw_command)

            self.broadcast("intent_detected", parsed)



            lifecycle.set_state(AssistantState.EXECUTING)

            self.broadcast("state_change", {"state": AssistantState.EXECUTING.value})



            # Execute

            result = ActionDispatcher.execute(parsed)



            # Broadcast result to GUI

            self.broadcast("command_result", {

                "raw_command": raw_command,

                "parsed": parsed,

                "result": result,

                "command_count": db.get_command_count()

            })



            return result

        finally:
            self._command_lock.release()



    def pause_listening(self):

        wakeword_listener.pause()

        self.broadcast("state_change", {"state": "PAUSED"})



    def resume_listening(self):

        wakeword_listener.resume()

        self.broadcast("state_change", {"state": AssistantState.ONLINE.value})



    def stop(self):

        self.is_running = False

        wakeword_listener.stop()

        battery_monitor.stop()

        connectivity_monitor.stop()

        tts.stop()

        lifecycle.set_state(AssistantState.OFFLINE)

        self.broadcast("state_change", {"state": AssistantState.OFFLINE.value})

        logger.info("DOOM AI Background Service stopped.")





# Global service daemon

background_service = BackgroundService()


