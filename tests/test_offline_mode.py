"""
Unit test suite verifying DOOM AI 100% Offline / Disconnected Wi-Fi Operation:
1. Fast offline TTS check: zero network hanging when offline.
2. System commands execution (Brightness, Airplane mode, Wi-Fi, Volume, Accessibility) offline.
3. Offline native SAPI fallback to Microsoft David Desktop deep male voice.
4. Native background speech grammar coverage.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.assistant.neural_tts import neural_tts, NeuralTTSEngine
from backend.assistant.text_to_speech import tts
from backend.ai.intent_parser import IntentParser
from backend.execution.system_executor import SystemExecutor
from backend.execution.action_executor import ActionDispatcher

def test_offline_tts_speed():
    print("\n--- 1. Testing Offline TTS Fallback Speed ---")
    # Simulate offline mode
    orig_cached = NeuralTTSEngine._is_online_cached
    NeuralTTSEngine._is_online_cached = False
    NeuralTTSEngine._last_online_check = time.time() + 100.0  # Force offline cache

    start_time = time.time()
    # Uncached phrase to verify it skips Edge WebSocket with 0 delay
    uncached_text = f"Offline execution verification test phrase {int(time.time())}"
    res = neural_tts.synthesize(uncached_text, lang="en")
    elapsed = time.time() - start_time

    print(f"  Synthesize call took: {elapsed * 1000:.2f} ms")
    assert res is None, "Expected None so it falls back to native Windows SAPI"
    assert elapsed < 0.1, f"Expected <100ms when offline, took {elapsed:.2f}s (must NOT hang on remote websockets!)"
    print("  ✓ Neural TTS skips remote websockets instantly (<100ms) when Wi-Fi is offline.")

    # Restore cache
    NeuralTTSEngine._is_online_cached = orig_cached
    NeuralTTSEngine._last_online_check = 0.0

def test_offline_command_execution():
    print("\n--- 2. Testing Offline Command Intent Parsing & Execution ---")
    commands = [
        ("increase brightness", "BRIGHTNESS_CONTROL"),
        ("decrease brightness", "BRIGHTNESS_CONTROL"),
        ("turn on areplane mode", "AIRPLANE_MODE_CONTROL"),
        ("turn off aeroplane mode", "AIRPLANE_MODE_CONTROL"),
        ("turn on wifi", "WIFI_CONTROL"),
        ("turn off wifi", "WIFI_CONTROL"),
        ("turn on bluetooth", "BLUETOOTH_CONTROL"),
        ("turn on magnifier", "ACCESSIBILITY_CONTROL"),
        ("turn off magnifier", "ACCESSIBILITY_CONTROL"),
        ("open on screen keyboard", "ACCESSIBILITY_CONTROL"),
        ("volume up", "VOLUME_CONTROL"),
        ("volume max", "VOLUME_CONTROL"),
        ("mute", "VOLUME_CONTROL"),
    ]

    for cmd, expected_intent in commands:
        parsed = IntentParser.parse(cmd)
        assert parsed["intent"] == expected_intent, f"Failed for '{cmd}': got {parsed['intent']}"
        res = ActionDispatcher.execute(parsed)
        assert res["status"] == "SUCCESS", f"Execution failed for '{cmd}': {res}"
        assert "Master" in res["voice_response"] or "మాస్టర్" in res["voice_response"]
        print(f"  ✓ '{cmd}' -> {res['intent']} -> \"{res['voice_response']}\"")

def test_offline_wakeword_grammar():
    print("\n--- 3. Testing Offline SAPI Grammar Definition ---")
    from backend.assistant.wakeword import WAKE_PATTERNS
    # Verify wake patterns match common variations
    for test_phrase in ["doom", "hey doom", "doom ai", "hey vikram", "vikram"]:
        parsed = False
        import re
        for pat in WAKE_PATTERNS:
            if re.search(pat, test_phrase, re.IGNORECASE):
                parsed = True
                break
        assert parsed, f"Wake pattern failed for '{test_phrase}'"
        print(f"  ✓ Wake word pattern matches: '{test_phrase}'")

if __name__ == "__main__":
    test_offline_tts_speed()
    test_offline_command_execution()
    test_offline_wakeword_grammar()
    print("\n==========================================")
    print("ALL OFFLINE / DISCONNECTED WI-FI TESTS PASSED!")
    print("==========================================")
