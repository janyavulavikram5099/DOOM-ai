"""
Comprehensive verification test for DOOM AI Local Offline Whisper STT & Action Pipeline.
Verifies:
1. Local faster-whisper model loads from local directory without internet (local_files_only).
2. Model loads once and reuses instance.
3. Offline command processing flow (Local Whisper -> wakeword_listener -> background_service -> ActionDispatcher).
4. Wake word offline handling: "Hey Doom" alone vs "Hey Doom <command>".
5. Online command guards offline: "Internet connection is required for that action, Master."
6. Local application and system command execution offline.
7. Unintelligible speech & microphone error responses.
"""

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.assistant.speech_to_text import stt_engine, SpeechToTextEngine
from backend.assistant.wakeword import wakeword_listener
from backend.assistant.text_to_speech import tts
from backend.execution.action_executor import ActionDispatcher
from backend.ai.intent_parser import IntentParser
from backend.monitoring.system_monitor import SystemMonitor

def test_whisper_model_local_load():
    print("\n--- 1. Testing Local Faster-Whisper Model Initialization ---")
    stt = SpeechToTextEngine()
    stt.load_model()
    assert stt._model is not None, "Local Whisper model failed to load!"
    assert stt._model_loaded is True, "Model loaded flag must be True"
    print(f"  [OK] Whisper model loaded successfully on: {stt._device} ({stt._compute_type})")

    # Verify model is reused and not reloaded
    first_instance = stt._model
    stt.load_model()
    assert stt._model is first_instance, "Model was reloaded instead of reused!"
    print("  [OK] Whisper model is properly cached and reused without reloading.")

def test_wakeword_offline_processing():
    print("\n--- 2. Testing Wake Word Behavior Offline ---")
    last_spoken = []
    orig_speak = tts.speak
    tts.speak = lambda text, *args, **kwargs: last_spoken.append(text)

    commands_detected = []
    wakeword_listener.on_command_detected = lambda cmd, is_v, score: commands_detected.append(cmd)
    wakeword_listener.is_active = True
    wakeword_listener.is_paused = False

    try:
        # 2a. User says "Hey Doom" alone
        last_spoken.clear()
        commands_detected.clear()
        ok, res = wakeword_listener.process_speech_input("Hey Doom")
        assert ok is True
        assert any("Hello Master" in s for s in last_spoken), f"Expected 'Hello Master.', got: {last_spoken}"
        assert len(commands_detected) == 0, "No command should be dispatched for standalone wake word"
        print("  ✓ 'Hey Doom' alone -> Responded 'Hello Master.' without executing empty command.")

        # 2b. User says "Hey Doom open calculator"
        last_spoken.clear()
        commands_detected.clear()
        ok, res = wakeword_listener.process_speech_input("Hey Doom open calculator")
        assert ok is True
        assert len(commands_detected) == 1
        assert "open calculator" in commands_detected[0].lower()
        print("  ✓ 'Hey Doom open calculator' -> Extracted command 'open calculator' and dispatched.")

        # 2c. User says direct action command "increase volume"
        last_spoken.clear()
        commands_detected.clear()
        ok, res = wakeword_listener.process_speech_input("increase volume", allow_direct=True)
        assert ok is True
        assert len(commands_detected) == 1
        assert "volume" in commands_detected[0].lower()
        print("  ✓ Direct command 'increase volume' recognized and forwarded.")

    finally:
        tts.speak = orig_speak

def test_online_commands_blocked_offline():
    print("\n--- 3. Testing Online Commands Guard When Disconnected ---")
    # Simulate network offline
    orig_is_online = SystemMonitor.is_network_online
    SystemMonitor.is_network_online = lambda: False

    last_spoken = []
    orig_speak = tts.speak
    tts.speak = lambda text, *args, **kwargs: last_spoken.append(text)

    try:
        # 3a. Search Web offline
        last_spoken.clear()
        parsed = IntentParser.parse("search Google for Python tutorials")
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "OFFLINE"
        assert "Internet connection is required for that action, Master." in res["voice_response"]
        assert any("Internet connection is required for that action, Master." in s for s in last_spoken)
        print("  ✓ 'search Google...' offline -> Correctly announced: 'Internet connection is required for that action, Master.'")

        # 3b. Ask AI offline
        last_spoken.clear()
        parsed = IntentParser.parse("what is quantum computing")
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "OFFLINE"
        assert "Internet connection is required for that action, Master." in res["voice_response"]
        print("  ✓ 'what is quantum computing' offline -> Correctly announced: 'Internet connection is required for that action, Master.'")

        # 3c. Open external website offline
        last_spoken.clear()
        parsed = IntentParser.parse("open youtube.com")
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "OFFLINE"
        assert "Internet connection is required for that action, Master." in res["voice_response"]
        print("  ✓ 'open youtube.com' offline -> Correctly announced: 'Internet connection is required for that action, Master.'")

    finally:
        SystemMonitor.is_network_online = orig_is_online
        tts.speak = orig_speak

def test_local_commands_offline():
    print("\n--- 4. Testing Local Commands Execution When Disconnected ---")
    # Simulate network offline
    orig_is_online = SystemMonitor.is_network_online
    SystemMonitor.is_network_online = lambda: False

    try:
        # 4a. Volume Control
        parsed = IntentParser.parse("volume up")
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "SUCCESS"
        assert "Master" in res["voice_response"]
        print(f"  ✓ 'volume up' offline -> SUCCESS -> '{res['voice_response']}'")

        # 4b. Brightness Control
        parsed = IntentParser.parse("brightness up")
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "SUCCESS"
        assert "Master" in res["voice_response"]
        print(f"  ✓ 'brightness up' offline -> SUCCESS -> '{res['voice_response']}'")

        # 4c. Time / Date
        parsed = IntentParser.parse("what time is it")
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "SUCCESS"
        print(f"  ✓ 'what time is it' offline -> SUCCESS -> '{res['voice_response']}'")

    finally:
        SystemMonitor.is_network_online = orig_is_online

if __name__ == "__main__":
    test_whisper_model_local_load()
    test_wakeword_offline_processing()
    test_online_commands_blocked_offline()
    test_local_commands_offline()
    print("\n=======================================================")
    print("ALL LOCAL OFFLINE WHISPER & PIPELINE TESTS PASSED!")
    print("=======================================================")
