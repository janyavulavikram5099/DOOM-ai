"""
Unit tests for DOOM AI Settings Control:
- Brightness (increase, decrease, set, max, min, check)
- Airplane / Aeroplane Mode (turn on, turn off, check)
- Accessibility (magnifier, narrator, on-screen keyboard, high contrast, general)
- Volume (increase, decrease, max, min, mute, unmute, set)
- Wi-Fi and Bluetooth
- Windows Settings pages
- Bilingual verification (English and Telugu)
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.intent_parser import IntentParser
from backend.execution.system_executor import SystemExecutor

def test_intent_parsing():
    test_cases = [
        # Brightness
        ("increase brigthness", "BRIGHTNESS_CONTROL", {"action": "up", "level": 15}),
        ("increase brightness", "BRIGHTNESS_CONTROL", {"action": "up", "level": 15}),
        ("decrease brigthness", "BRIGHTNESS_CONTROL", {"action": "down", "level": 15}),
        ("decrease brightness", "BRIGHTNESS_CONTROL", {"action": "down", "level": 15}),
        ("set brightness to 80%", "BRIGHTNESS_CONTROL", {"action": "set", "level": 80}),
        ("brightness max", "BRIGHTNESS_CONTROL", {"action": "max"}),
        ("min brightness", "BRIGHTNESS_CONTROL", {"action": "min"}),
        ("check brightness", "BRIGHTNESS_CONTROL", {"action": "status"}),

        # Airplane Mode (including user spelling variations)
        ("turn on areplane mode", "AIRPLANE_MODE_CONTROL", {"action": "on"}),
        ("turn on aeroplane mode", "AIRPLANE_MODE_CONTROL", {"action": "on"}),
        ("turn on airplane mode", "AIRPLANE_MODE_CONTROL", {"action": "on"}),
        ("turn off areplane mode", "AIRPLANE_MODE_CONTROL", {"action": "off"}),
        ("turn off aeroplane mode", "AIRPLANE_MODE_CONTROL", {"action": "off"}),
        ("turn off airplane mode", "AIRPLANE_MODE_CONTROL", {"action": "off"}),
        ("airplane mode status", "AIRPLANE_MODE_CONTROL", {"action": "status"}),

        # Accessibility
        ("turn on magnifier", "ACCESSIBILITY_CONTROL", {"action": "on", "feature": "magnifier"}),
        ("turn off magnifier", "ACCESSIBILITY_CONTROL", {"action": "off", "feature": "magnifier"}),
        ("turn on narrator", "ACCESSIBILITY_CONTROL", {"action": "on", "feature": "narrator"}),
        ("turn off narrator", "ACCESSIBILITY_CONTROL", {"action": "off", "feature": "narrator"}),
        ("open on screen keyboard", "ACCESSIBILITY_CONTROL", {"action": "on", "feature": "keyboard"}),
        ("close on screen keyboard", "ACCESSIBILITY_CONTROL", {"action": "off", "feature": "keyboard"}),
        ("open accessibility settings", "ACCESSIBILITY_CONTROL", {"action": "open", "feature": "general"}),

        # Wi-Fi & Bluetooth
        ("turn on wifi", "WIFI_CONTROL", {"action": "on"}),
        ("turn off wifi", "WIFI_CONTROL", {"action": "off"}),
        ("turn on bluetooth", "BLUETOOTH_CONTROL", {"action": "on"}),
        ("turn off bluetooth", "BLUETOOTH_CONTROL", {"action": "off"}),

        # Volume
        ("increase volume", "VOLUME_CONTROL", {"action": "up"}),
        ("decrease volume", "VOLUME_CONTROL", {"action": "down"}),
        ("volume max", "VOLUME_CONTROL", {"action": "max"}),
        ("volume min", "VOLUME_CONTROL", {"action": "min"}),
        ("mute", "VOLUME_CONTROL", {"action": "mute"}),
        ("unmute", "VOLUME_CONTROL", {"action": "unmute"}),
        ("set volume to 80%", "VOLUME_CONTROL", {"action": "set", "level": 80}),

        # Settings Pages
        ("open display settings", "OPEN_SETTINGS", {"setting": "display"}),
        ("open sound settings", "OPEN_SETTINGS", {"setting": "sound"}),
        ("open wifi settings", "OPEN_SETTINGS", {"setting": "wifi"}),
        ("open settings", "OPEN_SETTINGS", {"setting": "general"}),

        # Telugu / Tanglish
        ("brightness penchu", "BRIGHTNESS_CONTROL", {"action": "up", "level": 15}),
        ("brightness thagginchu", "BRIGHTNESS_CONTROL", {"action": "down", "level": 15}),
        ("aeroplane mode on cheyyi", "AIRPLANE_MODE_CONTROL", {"action": "on"}),
        ("aeroplane mode off cheyyi", "AIRPLANE_MODE_CONTROL", {"action": "off"}),
        ("magnifier on cheyyi", "ACCESSIBILITY_CONTROL", {"action": "on", "feature": "magnifier"}),
        ("wifi on cheyyi", "WIFI_CONTROL", {"action": "on"}),
    ]

    all_passed = True
    for text, expected_intent, expected_params in test_cases:
        res = IntentParser.parse(text)
        actual_intent = res.get("intent")
        actual_params = res.get("params", {})
        
        matches = (actual_intent == expected_intent)
        for k, v in expected_params.items():
            if actual_params.get(k) != v:
                matches = False
                break

        if matches:
            print(f"PASS: '{text}' -> {actual_intent} {actual_params}")
        else:
            print(f"FAIL: '{text}' -> expected {expected_intent} {expected_params}, got {actual_intent} {actual_params}")
            all_passed = False

    return all_passed

def test_executor_responses():
    print("\nTesting SystemExecutor responses (English & Telugu):")
    # Brightness
    ok, msg = SystemExecutor.brightness_control("up", 15, "en")
    print(f"Brightness UP (EN): {msg}")
    assert "Brightness increased" in msg and "Master" in msg

    ok, msg = SystemExecutor.brightness_control("down", 15, "en")
    print(f"Brightness DOWN (EN): {msg}")
    assert "Brightness decreased" in msg and "Master" in msg

    ok, msg = SystemExecutor.brightness_control("set", 80, "en")
    print(f"Brightness SET (EN): {msg}")
    assert "80 percent" in msg and "Master" in msg

    # Airplane Mode
    ok, msg = SystemExecutor.set_airplane_mode("on", "en")
    print(f"Airplane ON (EN): {msg}")
    assert "Airplane mode is now turned on" in msg and "Master" in msg

    ok, msg = SystemExecutor.set_airplane_mode("off", "en")
    print(f"Airplane OFF (EN): {msg}")
    assert "Airplane mode is now turned off" in msg and "Master" in msg

    # Volume
    ok, msg = SystemExecutor.volume_control("max", 100, "en")
    print(f"Volume MAX (EN): {msg}")
    assert "maximum" in msg and "Master" in msg

    # Telugu responses
    ok, msg = SystemExecutor.brightness_control("up", 15, "te")
    print(f"Brightness UP (TE): {msg}")
    assert "బ్రైట్‌నెస్" in msg and "మాస్టర్" in msg

    ok, msg = SystemExecutor.set_airplane_mode("on", "te")
    print(f"Airplane ON (TE): {msg}")
    assert "ఏరోప్లేన్ మోడ్" in msg and "మాస్టర్" in msg

    print("\nAll executor responses verified successfully!")
    return True

if __name__ == "__main__":
    p_ok = test_intent_parsing()
    e_ok = test_executor_responses()
    if p_ok and e_ok:
        print("\nALL SETTINGS CONTROL TESTS PASSED!")
    else:
        sys.exit(1)
