import sys
sys.path.insert(0, r"c:\Users\mones\OneDrive\Desktop\Vikram AI")

from backend.ai.intent_parser import IntentParser
from backend.execution.action_executor import ActionDispatcher

test_phrases = [
    "what is charging now",
    "doom what is charging now",
    "what is charging",
    "charging now",
    "how much is charging",
    "charging percentage",
    "what is the charging percentage",
    "battery percentage",
    "battery status"
]

for p in test_phrases:
    parsed = IntentParser.parse(p)
    print(f"{p:35} -> Intent: {parsed['intent']}, Params: {parsed.get('params')}")

res = ActionDispatcher.execute(IntentParser.parse("what is charging now"))
print("\nEXECUTION RESULT:")
print("Status:", res["status"])
print("Voice Response:", res["voice_response"])
