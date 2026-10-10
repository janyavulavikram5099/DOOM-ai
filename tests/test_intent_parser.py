"""
Unit tests for VIKRAM Natural Language Intent Parser.
"""

import unittest
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.intent_parser import IntentParser
from backend.assistant.conversation import conversation_context


class TestIntentParser(unittest.TestCase):
    def setUp(self):
        conversation_context.clear()

    def test_application_intents(self):
        phrases = [
            ("Open VS Code", "OPEN_APPLICATION"),
            ("Launch VS Code", "OPEN_APPLICATION"),
            ("Can you open Visual Studio Code?", "OPEN_APPLICATION"),
            ("I need VS Code", "OPEN_APPLICATION"),
            ("Start Visual Studio Code", "OPEN_APPLICATION"),
            ("Open Chrome", "OPEN_APPLICATION"),
            ("Close Chrome", "CLOSE_APPLICATION"),
            ("close whatsapp", "CLOSE_APPLICATION"),
            ("close the whatsapp", "CLOSE_APPLICATION"),
            ("close whatsapp please", "CLOSE_APPLICATION"),
            ("quit whatsapp", "CLOSE_APPLICATION"),
            ("exit file explorer", "CLOSE_APPLICATION"),
            ("close file explore", "CLOSE_APPLICATION"),
            ("close whatsapp application", "CLOSE_APPLICATION"),
        ]
        for phrase, expected_intent in phrases:
            result = IntentParser.parse(phrase)
            self.assertEqual(result["intent"], expected_intent, f"Failed for phrase: {phrase}")

    def test_browser_and_search_intents(self):
        res1 = IntentParser.parse("open YouTube in Chrome")
        self.assertEqual(res1["intent"], "OPEN_WEBSITE")
        self.assertEqual(res1["params"].get("website").lower(), "youtube")
        self.assertEqual(res1["params"].get("browser").lower(), "chrome")

        res2 = IntentParser.parse("search Google for Java multithreading")
        self.assertEqual(res2["intent"], "SEARCH_WEB")
        self.assertEqual(res2["params"].get("query"), "Java multithreading")

    def test_system_lock_intent(self):
        res = IntentParser.parse("Hey Vikram, lock my laptop")
        res2 = IntentParser.parse("lock my laptop")
        self.assertEqual(res2["intent"], "LOCK_DEVICE")

    def test_system_unlock_intent(self):
        res_unlock = IntentParser.parse("unlock my laptop")
        self.assertEqual(res_unlock["intent"], "UNLOCK_DEVICE")
        res_unlock_short = IntentParser.parse("unlock")
        self.assertEqual(res_unlock_short["intent"], "UNLOCK_DEVICE")

    def test_date_and_time_intents(self):
        res_time = IntentParser.parse("what is the time")
        self.assertEqual(res_time["intent"], "GET_DATE_TIME")
        self.assertEqual(res_time["params"].get("type"), "time")

        res_date = IntentParser.parse("doom what is today's date")
        self.assertEqual(res_date["intent"], "GET_DATE_TIME")
        self.assertEqual(res_date["params"].get("type"), "date")

        res_both = IntentParser.parse("tell me date and time")
        self.assertEqual(res_both["intent"], "GET_DATE_TIME")
        self.assertEqual(res_both["params"].get("type"), "both")

    def test_wifi_control_intents(self):
        res_on = IntentParser.parse("doom turn on wifi")
        self.assertEqual(res_on["intent"], "WIFI_CONTROL")
        self.assertEqual(res_on["params"].get("action"), "on")

        res_off = IntentParser.parse("turn off wifi")
        self.assertEqual(res_off["intent"], "WIFI_CONTROL")
        self.assertEqual(res_off["params"].get("action"), "off")

    def test_bluetooth_control_intents(self):
        res_on = IntentParser.parse("doom turn on bluetooth")
        self.assertEqual(res_on["intent"], "BLUETOOTH_CONTROL")
        self.assertEqual(res_on["params"].get("action"), "on")

        res_off = IntentParser.parse("turn off bluetooth")
        self.assertEqual(res_off["intent"], "BLUETOOTH_CONTROL")
        self.assertEqual(res_off["params"].get("action"), "off")

    def test_email_and_explorer_intents(self):
        res_mail = IntentParser.parse("open my email")
        self.assertEqual(res_mail["intent"], "OPEN_WEBSITE")
        self.assertEqual(res_mail["params"].get("website"), "gmail")

        res_exp = IntentParser.parse("open file explore")
        self.assertEqual(res_exp["intent"], "OPEN_APPLICATION")
        self.assertEqual(res_exp["params"].get("app_name"), "file explorer")

    def test_developer_mode_and_context(self):
        res = IntentParser.parse("compile Hello.java")
        self.assertEqual(res["intent"], "COMPILE_CODE")
        self.assertEqual(res["params"].get("file_name"), "Hello.java")

        # Set context
        conversation_context.update(current_file="Hello.java", current_language="java")
        res_it = IntentParser.parse("compile it")
        self.assertEqual(res_it["intent"], "COMPILE_CODE")
        self.assertEqual(res_it["params"].get("file_name"), "Hello.java")

    def test_telemetry_intents(self):
        res_cpu = IntentParser.parse("what's my CPU usage?")
        self.assertEqual(res_cpu["intent"], "SYSTEM_INFO")
        self.assertEqual(res_cpu["params"].get("metric"), "cpu")


if __name__ == "__main__":
    unittest.main()
