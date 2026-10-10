from backend.ai.intent_parser import IntentParser

commands = [
    "open file explore",
    "open file explorer",
    "open files",
    "file explorer",
    "file explore",
    "open chrome",
    "open google chrome",
    "open edge",
    "open microsoft edge",
    "open whatsapp",
    "open whatsup",
    "open settings",
    "open windows settings",
    "open store",
    "open microsoft store",
    "open copilot",
    "open lenovo vantage",
    "open vantage",
    "open outlook",
    "open notepad",
    "open calculator",
    "open calc",
    "open vscode",
    "open vs code",
    "open visual studio code",
    "hey vikram open file explore",
    "hey vikram open chrome",
    "hey vikram open whatsapp",
    "hey vikram open settings",
    "hey vikram open store",
    "hey vikram open copilot"
]

print("--- Testing Intent Parser ---")
for cmd in commands:
    res = IntentParser.parse(cmd)
    intent = res.get("intent")
    params = res.get("params")
    print(f"'{cmd}' -> {intent} | {params}")
