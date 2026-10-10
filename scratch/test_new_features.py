import sys
import os

sys.path.insert(0, r"c:\Users\mones\OneDrive\Desktop\Vikram AI")

from backend.ai.intent_parser import IntentParser
from backend.execution.action_executor import ActionDispatcher
from backend.execution.system_executor import SystemExecutor

print("=== 1. TESTING INTENT PARSER ===")
test_queries = [
    # Time
    ("what is the time", "GET_DATE_TIME", "time"),
    ("doom what time is it", "GET_DATE_TIME", "time"),
    ("tell me the time", "GET_DATE_TIME", "time"),
    ("hey doom, time", "GET_DATE_TIME", "time"),
    # Date
    ("what is the date", "GET_DATE_TIME", "date"),
    ("doom what is today's date", "GET_DATE_TIME", "date"),
    ("tell me today's date", "GET_DATE_TIME", "date"),
    ("hey doom, date", "GET_DATE_TIME", "date"),
    # Both
    ("what is the date and time", "GET_DATE_TIME", "both"),
    ("doom tell me the date and time", "GET_DATE_TIME", "both"),
    # Wi-Fi
    ("turn on wifi", "WIFI_CONTROL", "on"),
    ("doom turn on wifi", "WIFI_CONTROL", "on"),
    ("turn off wifi", "WIFI_CONTROL", "off"),
    ("doom turn off wifi", "WIFI_CONTROL", "off"),
    ("wifi status", "WIFI_CONTROL", "status"),
    # Bluetooth
    ("turn on bluetooth", "BLUETOOTH_CONTROL", "on"),
    ("doom turn on bluetooth", "BLUETOOTH_CONTROL", "on"),
    ("turn off bluetooth", "BLUETOOTH_CONTROL", "off"),
    ("doom turn off bluetooth", "BLUETOOTH_CONTROL", "off"),
    ("bluetooth status", "BLUETOOTH_CONTROL", "status"),
]

all_passed = True
for query, expected_intent, expected_param in test_queries:
    parsed = IntentParser.parse(query)
    intent = parsed.get("intent")
    params = parsed.get("params", {})
    param_val = params.get("type") or params.get("action")
    if intent == expected_intent and param_val == expected_param:
        print(f"  [PASS] '{query}' -> {intent} ({param_val})")
    else:
        print(f"  [FAIL] '{query}' -> Got {intent} ({param_val}), Expected {expected_intent} ({expected_param})")
        all_passed = False

print("\n=== 2. TESTING SYSTEM EXECUTOR DATE/TIME ===")
ok, time_msg, details = SystemExecutor.get_date_time("time")
print("  Time response:", time_msg)
ok, date_msg, details = SystemExecutor.get_date_time("date")
print("  Date response:", date_msg)
ok, both_msg, details = SystemExecutor.get_date_time("both")
print("  Both response:", both_msg)

print("\n=== 3. TESTING RADIO STATUS ===")
ok, wifi_status = SystemExecutor.set_wifi_state("status")
print(f"  Wi-Fi Status: {wifi_status} (ok={ok})")
ok, bt_status = SystemExecutor.set_bluetooth_state("status")
print(f"  Bluetooth Status: {bt_status} (ok={ok})")

print("\n=== 4. TESTING ACTION DISPATCHER VIA MOCK COMMANDS ===")
res_time = ActionDispatcher.execute({"intent": "GET_DATE_TIME", "raw_text": "what time is it", "params": {"type": "time"}})
print("  ActionDispatcher (time):", res_time["voice_response"])

res_date = ActionDispatcher.execute({"intent": "GET_DATE_TIME", "raw_text": "what is today's date", "params": {"type": "date"}})
print("  ActionDispatcher (date):", res_date["voice_response"])

if all_passed:
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
else:
    print("\n>>> SOME TESTS FAILED <<<")
