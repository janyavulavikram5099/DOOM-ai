"""
VIKRAM / DOOM AI - Bilingual Telugu & English Intelligence Verification Test Suite.
Tests:
1. Telugu Unicode script command parsing
2. Transliterated Tanglish command parsing
3. English command parsing
4. Natural Telugu response generation
5. Neural TTS audio synthesis
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.ai.language_detector import detect_language, is_telugu_lang, is_english
from backend.ai.telugu_engine import telugu_engine, is_telugu
from backend.ai.intent_parser import IntentParser
from backend.assistant.neural_tts import neural_tts


def test_language_detection():
    print("\n--- Testing Language Detection ---")
    telugu_samples = [
        "వాట్సాప్ ఓపెన్ చెయ్యి",
        "whatsapp open cheyyi",
        "settings close chey",
        "amma ki message pettu",
        "time entha",
        "battery entha undi",
        "nuvvu evaru",
        "ela unnavu"
    ]
    for s in telugu_samples:
        lang = detect_language(s)
        assert lang == "te", f"Expected 'te' for '{s}', got '{lang}'"
        assert is_telugu_lang(lang), f"Expected is_telugu_lang True for '{s}'"
        print(f"  ✓ '{s}' -> {lang} (Telugu)")

    english_samples = [
        "open whatsapp",
        "close settings",
        "lock my laptop",
        "what is the time",
        "check my battery percentage",
        "who are you",
        "how are you"
    ]
    for s in english_samples:
        lang = detect_language(s)
        assert lang == "en", f"Expected 'en' for '{s}', got '{lang}'"
        assert is_english(lang), f"Expected is_english True for '{s}'"
        print(f"  ✓ '{s}' -> {lang} (English)")


def test_telugu_script_commands():
    print("\n--- Testing Telugu Script Command Parsing ---")
    test_cases = [
        ("వాట్సాప్ ఓపెన్ చెయ్యి", "OPEN_APPLICATION", {"app_name": "whatsapp"}),
        ("సెట్టింగ్స్ క్లోజ్ చెయ్యి", "CLOSE_APPLICATION", {"app_name": "settings"}),
        ("ల్యాప్‌టాప్ లాక్ చెయ్యి", "LOCK_DEVICE", {}),
        ("సమయం ఎంత", "GET_DATE_TIME", {"type": "time"}),
        ("బ్యాటరీ ఎంత ఉంది", "SYSTEM_INFO", {"metric": "battery"}),
        ("వాల్యూమ్ పెంచు", "VOLUME_CONTROL", {"action": "up"}),
        ("వైఫై ఆన్ చెయ్యి", "WIFI_CONTROL", {"action": "on"}),
        ("బ్లూటూత్ ఆఫ్ చెయ్యి", "BLUETOOTH_CONTROL", {"action": "off"}),
        ("బ్రైట్‌నెస్ పెంచు", "BRIGHTNESS_CONTROL", {"action": "up"}),
        ("ఏరోప్లేన్ మోడ్ ఆన్", "AIRPLANE_MODE_CONTROL", {"action": "on"}),
        ("నమస్కారం", "GREETING", {}),
        ("అమ్మకి హాయ్ అని మెసేజ్ పెట్టు", "EXECUTE_TASK_PLAN", {"target_app": "whatsapp"}),
    ]

    for query, expected_intent, expected_params in test_cases:
        parsed = IntentParser.parse(query)
        assert parsed["intent"] == expected_intent, f"For '{query}': expected intent {expected_intent}, got {parsed['intent']}"
        assert parsed.get("language") == "te", f"For '{query}': expected language 'te', got {parsed.get('language')}"
        if expected_intent == "OPEN_APPLICATION" or expected_intent == "CLOSE_APPLICATION":
            assert parsed["params"]["app_name"] == expected_params["app_name"]
        elif expected_intent == "EXECUTE_TASK_PLAN":
            assert parsed["params"]["plan"].target_app == expected_params["target_app"]
        print(f"  ✓ '{query}' -> {parsed['intent']} (Language: {parsed.get('language')})")


def test_tanglish_commands():
    print("\n--- Testing Tanglish Command Parsing ---")
    test_cases = [
        ("whatsapp open cheyyi", "OPEN_APPLICATION", {"app_name": "whatsapp"}),
        ("settings close cheyyi", "CLOSE_APPLICATION", {"app_name": "settings"}),
        ("laptop lock cheyyi", "LOCK_DEVICE", {}),
        ("time entha", "GET_DATE_TIME", {"type": "time"}),
        ("battery entha undi", "SYSTEM_INFO", {"metric": "battery"}),
        ("volume thagginchu", "VOLUME_CONTROL", {"action": "down"}),
        ("wifi on cheyyi", "WIFI_CONTROL", {"action": "on"}),
        ("bluetooth off chey", "BLUETOOTH_CONTROL", {"action": "off"}),
        ("brightness penchu", "BRIGHTNESS_CONTROL", {"action": "up"}),
        ("aeroplane mode on cheyyi", "AIRPLANE_MODE_CONTROL", {"action": "on"}),
        ("namaskaram", "GREETING", {}),
        ("amma ki hi ani message pettu", "EXECUTE_TASK_PLAN", {"target_app": "whatsapp"}),
    ]

    for query, expected_intent, expected_params in test_cases:
        parsed = IntentParser.parse(query)
        assert parsed["intent"] == expected_intent, f"For '{query}': expected intent {expected_intent}, got {parsed['intent']}"
        assert parsed.get("language") == "te", f"For '{query}': expected language 'te', got {parsed.get('language')}"
        print(f"  ✓ '{query}' -> {parsed['intent']} (Language: {parsed.get('language')})")


def test_english_commands():
    print("\n--- Testing English Command Parsing ---")
    test_cases = [
        ("open whatsapp", "OPEN_APPLICATION"),
        ("open settings", "OPEN_SETTINGS"),
        ("settings", "OPEN_SETTINGS"),
        ("open setting", "OPEN_SETTINGS"),
        ("open windows settings", "OPEN_SETTINGS"),
        ("all been sitting", "OPEN_SETTINGS"),
        ("open sitting", "OPEN_SETTINGS"),
        ("close settings", "CLOSE_APPLICATION"),
        ("settings close", "CLOSE_APPLICATION"),
        ("close window", "CLOSE_APPLICATION"),
        ("close the window", "CLOSE_APPLICATION"),
        ("close", "CLOSE_APPLICATION"),
        ("close it", "CLOSE_APPLICATION"),
        ("close this", "CLOSE_APPLICATION"),
        ("close tab", "CLOSE_APPLICATION"),
        ("close all", "CLOSE_APPLICATION"),
        ("close all apps", "CLOSE_APPLICATION"),
        ("close everything", "CLOSE_APPLICATION"),
        ("close whatsapp", "CLOSE_APPLICATION"),
        ("close chrome", "CLOSE_APPLICATION"),
        ("clothes window", "CLOSE_APPLICATION"),
        ("closed settings", "CLOSE_APPLICATION"),
        ("close sitting", "CLOSE_APPLICATION"),
        ("NBA", "UNKNOWN"),
        ("at the", "UNKNOWN"),
        ("what is quantum computing", "ASK_AI"),
        ("lock laptop", "LOCK_DEVICE"),
        ("what is the time", "GET_DATE_TIME"),
        ("battery percentage", "SYSTEM_INFO"),
        ("turn on wifi", "WIFI_CONTROL"),
        ("turn off bluetooth", "BLUETOOTH_CONTROL"),
        ("increase brigthness", "BRIGHTNESS_CONTROL"),
        ("decrease brightness", "BRIGHTNESS_CONTROL"),
        ("turn on areplane mode", "AIRPLANE_MODE_CONTROL"),
        ("turn off aeroplane mode", "AIRPLANE_MODE_CONTROL"),
        ("turn on magnifier", "ACCESSIBILITY_CONTROL"),
        ("search python", "ASK_AI"),
        ("search about quantum computing", "ASK_AI"),
        ("search in google what is an operating system", "ASK_AI"),
        ("search on google for machine learning", "ASK_AI"),
        ("search for artificial intelligence", "ASK_AI"),
        ("search that", "ASK_AI"),
        ("search about that", "ASK_AI"),
        ("search", "ASK_AI"),
        ("google machine learning", "ASK_AI"),
        ("search youtube for coldplay", "SEARCH_WEB"),
        ("search files notes.txt", "SEARCH_FILES"),
        ("hello", "GREETING"),
    ]

    for query, expected_intent in test_cases:
        parsed = IntentParser.parse(query)
        assert parsed["intent"] == expected_intent, f"For '{query}': expected intent {expected_intent}, got {parsed['intent']}"
        assert parsed.get("language", "en") == "en"
        print(f"  ✓ '{query}' -> {parsed['intent']} (Language: en)")


def test_telugu_responses():
    print("\n--- Testing Telugu Natural Responses ---")
    # Launch
    r_launch = telugu_engine.get_response("OPEN_APPLICATION", {"app_name": "whatsapp"})
    assert "వాట్సాప్" in r_launch or "Whatsapp" in r_launch
    assert "ఓపెన్ చేస్తున్నాను" in r_launch
    assert "మాస్టర్" in r_launch
    print(f"  ✓ Launch: '{r_launch}'")

    # Close
    r_close = telugu_engine.get_response("CLOSE_APPLICATION", {"app_name": "settings"})
    assert "క్లోజ్ చేశాను" in r_close
    assert "మాస్టర్" in r_close
    print(f"  ✓ Close: '{r_close}'")

    # Lock
    r_lock = telugu_engine.get_response("LOCK_DEVICE", {})
    assert "లాక్ చేస్తున్నాను" in r_lock
    assert "మాస్టర్" in r_lock
    print(f"  ✓ Lock: '{r_lock}'")

    # Greeting
    r_greet = telugu_engine.get_response("GREETING", {})
    assert "నమస్కారం" in r_greet
    assert "మాస్టర్" in r_greet
    print(f"  ✓ Greeting: '{r_greet}'")


def test_neural_tts_synthesis():
    print("\n--- Testing Neural TTS Synthesis ---")
    # Telugu
    te_text = "వాట్సాప్ ఓపెన్ చేస్తున్నాను, మాస్టర్."
    te_audio = neural_tts.synthesize(te_text, lang="te")
    if te_audio:
        assert os.path.exists(te_audio), f"Telugu audio file not found at {te_audio}"
        print(f"  ✓ Telugu Neural Audio: '{te_audio}' ({os.path.getsize(te_audio)} bytes)")

    # English Entry Greetings (Prewarmed Deep Male Voices)
    for entry_phrase in ["Hello Master.", "At your service, Master.", "Locking your laptop, Master."]:
        audio = neural_tts.synthesize(entry_phrase, lang="en")
        if audio:
            assert os.path.exists(audio)
            print(f"  ✓ English Neural Deep Male Audio: '{entry_phrase}' -> '{audio}' ({os.path.getsize(audio)} bytes)")


if __name__ == "__main__":
    test_language_detection()
    test_telugu_script_commands()
    test_tanglish_commands()
    test_english_commands()
    test_telugu_responses()
    test_neural_tts_synthesis()
    print("\n==========================================")
    print("ALL BILINGUAL TELUGU & ENGLISH TESTS PASSED!")
    print("==========================================")
