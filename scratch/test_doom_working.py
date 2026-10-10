"""
Instant verification test for DOOM AI working architecture in chat_engine.
"""
import sys
import time
import backend.ai.chat_engine as chat_mod
from backend.ai.chat_engine import chat_engine
from backend.assistant.text_to_speech import tts

# Mock TTS and sleep for instant test execution
tts.speak = lambda text: None
tts.speak_multilingual = lambda text, lang: None
time.sleep = lambda s: None

test_prompts = [
    "Doom Ai working a Gemini Ai",
    "how do you work",
    "how does doom ai work",
    "doom ai working",
    "explain your working"
]

for prompt in test_prompts:
    streamed_tokens = []
    def mock_broadcast(evt, data):
        if evt == "chat_stream_token":
            streamed_tokens.append(data["token"])

    chat_engine.set_broadcast_callback(mock_broadcast)
    res = chat_engine.process_prompt(prompt)
    answer = res["answer"]
    tts_ans = res["tts_answer"]

    print(f"\n======================================")
    print(f"QUERY: '{prompt}'")
    print(f"STATUS: {res['status']}")
    print(f"STREAMED TOKENS: {len(streamed_tokens)}")
    print(f"TTS SUMMARY: {tts_ans}")

    assert "Step 1: The Input Stage" in answer, f"Missing Step 1 in response for prompt: {prompt}"
    assert "Step 2: The Processing Stage" in answer, f"Missing Step 2 in response for prompt: {prompt}"
    assert "Step 3: The Output Stage" in answer, f"Missing Step 3 in response for prompt: {prompt}"
    assert "Live Web Grounding" in answer, f"Missing Live Web Grounding in response for prompt: {prompt}"
    assert "Pro Tip" in answer, f"Missing Pro Tip in response for prompt: {prompt}"
    assert "I operate in three stages, Master:" in tts_ans, f"Incorrect TTS summary: {tts_ans}"

print("\n>>> ALL DOOM AI WORKING TESTS PASSED PERFECTLY! <<<")
