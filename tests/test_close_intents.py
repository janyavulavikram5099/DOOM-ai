import unittest
from backend.ai.intent_parser import IntentParser

class TestCloseIntents(unittest.TestCase):
    def test_close_and_open_variants(self):
        cases = [
            ("close whatsapp", "CLOSE_APPLICATION", "whatsapp"),
            ("hey vikram close whatsapp", "CLOSE_APPLICATION", "whatsapp"),
            ("vikram close whatsapp", "CLOSE_APPLICATION", "whatsapp"),
            ("close the whatsapp", "CLOSE_APPLICATION", "whatsapp"),
            ("close chrome", "CLOSE_APPLICATION", "chrome"),
            ("hey vikram close chrome", "CLOSE_APPLICATION", "chrome"),
            ("close file explorer", "CLOSE_APPLICATION", "file explorer"),
            ("close file explore", "CLOSE_APPLICATION", "file explore"),
            ("close files", "CLOSE_APPLICATION", "files"),
            ("open whatsapp", "OPEN_APPLICATION", "whatsapp"),
            ("hey vikram open whatsapp", "OPEN_APPLICATION", "whatsapp"),
            ("close notepad", "CLOSE_APPLICATION", "notepad"),
            ("close roblox", "CLOSE_APPLICATION", "roblox"),
            ("close robolox", "CLOSE_APPLICATION", "robolox"),
            ("close roblox player", "CLOSE_APPLICATION", "roblox player"),
            ("open robolox", "OPEN_APPLICATION", "robolox"),
            ("open roblox player", "OPEN_APPLICATION", "roblox player"),
        ]
        for text, expected_intent, expected_app in cases:
            res = IntentParser.parse(text)
            self.assertEqual(res["intent"], expected_intent, f"Failed for {text}")
            self.assertEqual(res["params"].get("app_name"), expected_app, f"Failed app for {text}")

if __name__ == "__main__":
    unittest.main()
