"""
Test script to verify Gemini-style answering in DOOM AI.
"""

import time
import backend.ai.chat_engine as chat_mod
from backend.ai.chat_engine import chat_engine
from backend.assistant.text_to_speech import tts
from backend.database.sqlite import db

# Mock TTS and sleep for fast testing
tts.speak = lambda text: None
tts.speak_multilingual = lambda text, lang: None
time.sleep = lambda s: None

test_cases = [
    {
        "query": "what is overloading in java",
        "expect_in_answer": ["Method Overloading in Java", "Compile-Time", "Code Demonstration (JAVA)", "Calculator"],
        "expect_in_tts": "polymorphism"
    },
    {
        "query": "explain what",
        "expect_in_answer": ["Could you please specify which concept or topic", "What is overloading in Java?"],
        "expect_in_tts": "Could you please specify"
    },
    {
        "query": "what is photosynthesis",
        "expect_in_answer": ["Photosynthesis", "Sunlight", "Significance & Impact"],
        "expect_in_tts": "Photosynthesis"
    },
    {
        "query": "what is quantum computing",
        "expect_in_answer": ["Quantum", "Source reference:"],
        "expect_in_tts": "quantum"
    }
]

print("=== STARTING GEMINI-STYLE ANSWER TESTS ===")

for tc in test_cases:
    q = tc["query"]
    res = chat_engine.process_prompt(q)
    ans = res["answer"]
    tts_ans = res["tts_answer"]

    print(f"\n----------------------------------------")
    print(f"QUERY: '{q}'")
    print(f"STATUS: {res['status']}")
    print(f"TTS SUMMARY: {tts_ans}")
    print(f"ANSWER HEAD:\n{ans[:160]}...")

    for expected in tc["expect_in_answer"]:
        assert expected.lower() in ans.lower(), f"Expected '{expected}' in answer for query: '{q}'"

    assert tc["expect_in_tts"].lower() in tts_ans.lower(), f"Expected '{tc['expect_in_tts']}' in TTS for query: '{q}'"

# Test Setting Gemini API Key via Command
res_key = chat_engine.process_prompt("set gemini api key AIzaSyTestKey123")
assert "registered" in res_key["answer"].lower()
assert db.get_setting("gemini_api_key") == "AIzaSyTestKey123"

# Reset key back to empty for tests
db.set_setting("gemini_api_key", "")
assert db.get_setting("gemini_api_key") == ""

print("\n>>> ALL GEMINI-STYLE ANSWER TESTS PASSED PERFECTLY! <<<")
