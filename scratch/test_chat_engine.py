"""
Test script to verify LLM token-by-token streaming generation in chat_engine.
"""

from backend.ai.chat_engine import chat_engine

tokens = []
def mock_broadcast(evt, data):
    if evt == "chat_stream_token":
        tokens.append(data["token"])
    elif evt == "chat_stream_start":
        print("[STREAM START]:", data)
    elif evt == "chat_stream_end":
        print("[STREAM END]: Full text length =", len(data["full_text"]))

chat_engine.set_broadcast_callback(mock_broadcast)

res = chat_engine.process_prompt("Who are you and how can you help me?")
print("Result status:", res["status"])
print("Tokens streamed count:", len(tokens))
print("Sample streamed tokens:", tokens[:8])
print("TTS voice summary:", res["tts_answer"])
assert len(tokens) > 0, "Expected tokens to be streamed!"
assert "VIKRAM" in res["answer"], f"Expected Vikram in answer, got: {res['answer']}"
print("CHAT ENGINE TOKEN-BY-TOKEN TEST PASSED!")
