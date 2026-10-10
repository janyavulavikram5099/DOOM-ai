"""
VIKRAM AI - Natural Language Intent Parser
Parses human speech/text into structured, validated intent actions.
Supports context resolution ("compile it"), multi-turn queries, fuzzy entity mapping,
multilingual question detection, and AI-powered Q&A via Google Search + Gemini.
Preserves original parameter casing using case-insensitive regex matching on raw text.
"""

import logging
import re
from typing import Any

from ..assistant.conversation import conversation_context
from ..security.confirmation import confirmation_gate
from .task_planner import task_planner
from .telugu_engine import telugu_engine, is_telugu

logger = logging.getLogger("vikram.ai.intent_parser")

# Question trigger words — any phrase starting with these routes to ASK_AI
_QUESTION_PREFIXES = (
    "what ", "what's ", "whats ", "what is ", "what are ",
    "how ", "how do ", "how does ", "how to ", "how can ",
    "why ", "why is ", "why does ", "why do ",
    "explain ", "explain the ", "explain what ", "explain how ",
    "tell me ", "tell me about ", "tell me what ",
    "define ", "definition of ", "meaning of ",
    "is there ", "is it ", "can you explain ", "can you tell ",
    "difference between ", "what happens ", "when does ",
    "who is ", "who was ", "where is ", "which is ",
    "google ",
    "movie review ", "film review ", "review ", "reviews ",
    "suggest ", "recommend ", "give me ", "give ", "write ",
    "describe ", "details of ", "details about ", "history of ",
    "information on ", "information about ",
)


class IntentParser:
    @classmethod
    def parse(cls, text: str) -> dict[str, Any]:
        """Parses natural language text into a structured intent with parameters."""
        res = cls._parse_impl(text)
        if "language" not in res:
            res["language"] = "en"
        return res

    @classmethod
    def _parse_impl(cls, text: str) -> dict[str, Any]:
        raw = text.strip()
        clean = raw.lower()

        # 1. Check if this is an answer to a pending confirmation gate
        if confirmation_gate.has_pending():
            affirmatives = ["yes", "proceed", "continue", "confirm", "do it", "sure", "affirmative", "go ahead"]
            negatives = ["no", "cancel", "stop", "abort", "don't", "dont", "negative"]
            if any(w in clean for w in affirmatives):
                return {
                    "intent": "CONFIRM_ACTION",
                    "raw_text": raw,
                    "params": {"decision": True}
                }
            elif any(w in clean for w in negatives):
                return {
                    "intent": "CANCEL_ACTION",
                    "raw_text": raw,
                    "params": {"decision": False}
                }

        # Strip wake prefix if present: Telugu and English wake words
        wake_match = re.match(
            r"^(?:హే\s*డూమ్|డూమ్\s*ఏఐ|డూమ్|నమస్తే\s*డూమ్|నమస్కారం\s*డూమ్|ఓయ్\s*డూమ్|"
            r"hey\s+doom|hi\s+doom|hello\s+doom|ok\s+doom|okay\s+doom|doom\s+ai|doom|"
            r"hey\s+vikram|hi\s+vikram|hello\s+vikram|ok\s+vikram|okay\s+vikram|vikram|bikram|vicram)\s*[,:\-]?\s*",
            clean,
            re.IGNORECASE
        )
        if wake_match:
            stripped = clean[wake_match.end():].strip()
            if stripped:
                clean = stripped
                raw = raw[wake_match.end():].strip()

        # Check Telugu and Tanglish commands only if query is in Telugu / Tanglish
        if is_telugu(raw):
            telugu_cmd = telugu_engine.parse_command(raw)
            if telugu_cmd:
                logger.info(f"Telugu command parsed: {telugu_cmd.get('intent')} for query: '{raw}'")
                return telugu_cmd

        # 2. Greetings & Salutations (matches standalone greeting only)
        standalone_greetings = [
            "hwy", "hey", "hi", "hello", "doom", "hey doom", "doom ai", "hey doom ai",
            "vikram", "hey vikram", "good morning", "good evening", "how are you", "who are you",
            "what's up", "whats up"
        ]
        if clean in standalone_greetings:
            return {"intent": "GREETING", "raw_text": raw, "params": {}}

        # 3. System Unlock & Lock (Unlock checked before Lock to prevent substring collision)
        unlock_phrases = [
            "unlock", "unlock device", "unlock screen", "unlock my screen", "unlock laptop", "unlock my laptop",
            "unlock the laptop", "unlock computer", "unlock pc", "unlock my pc", "wake up", "wake up screen", "wake up laptop", "unlock it",
            "8055", "pin 8055", "unlock with 8055", "unlock using 8055", "unlock with pin", "enter pin 8055"
        ]
        if any(w in clean for w in unlock_phrases):
            return {"intent": "UNLOCK_DEVICE", "raw_text": raw, "params": {}}

        lock_phrases = [
            "lock device", "lock screen", "lock my screen", "lock laptop", "lock my laptop",
            "lock the laptop", "lock computer", "lock pc", "lock my pc", "lock session", "lock workstation", "lock it"
        ]
        is_lock_cmd = ("unlock" not in clean) and (clean == "lock" or any(w in clean for w in lock_phrases) or bool(re.search(r"\block\b", clean)))
        if is_lock_cmd and not any(w in clean for w in ["clock", "o'clock", "block"]):
            return {"intent": "LOCK_DEVICE", "raw_text": raw, "params": {}}

        if any(w in clean for w in ["sleep my laptop", "sleep laptop", "put computer to sleep", "sleep pc"]):
            return {"intent": "SLEEP_DEVICE", "raw_text": raw, "params": {}}

        if any(w in clean for w in ["restart my laptop", "restart laptop", "reboot computer", "restart pc"]):
            return {"intent": "RESTART_DEVICE", "raw_text": raw, "params": {}}

        if any(w in clean for w in ["shutdown my laptop", "shutdown laptop", "turn off computer", "shutdown pc", "shut down"]):
            return {"intent": "SHUTDOWN_DEVICE", "raw_text": raw, "params": {}}

        # 3. Screenshot
        if any(w in clean for w in ["take screenshot", "take a screenshot", "capture screen", "capture my screen", "screen grab"]):
            return {"intent": "SCREENSHOT", "raw_text": raw, "params": {}}

        # 4. System Telemetry & Status
        if any(w in clean for w in ["cpu usage", "what's my cpu", "how is my cpu", "cpu percentage"]):
            return {"intent": "SYSTEM_INFO", "raw_text": raw, "params": {"metric": "cpu"}}

        if any(w in clean for w in ["ram usage", "memory usage", "what's my ram", "how much ram"]):
            return {"intent": "SYSTEM_INFO", "raw_text": raw, "params": {"metric": "ram"}}

        if any(w in clean for w in ["gpu usage", "what's my gpu", "graphics usage"]):
            return {"intent": "SYSTEM_INFO", "raw_text": raw, "params": {"metric": "gpu"}}

        if any(w in clean for w in ["storage", "disk usage", "how much storage", "hard drive space"]):
            return {"intent": "SYSTEM_INFO", "raw_text": raw, "params": {"metric": "storage"}}

        # Battery & Charging Telemetry (Instant hardware query)
        clean_no_punct = clean.rstrip("?.! ")
        is_charge_word = any(w in clean_no_punct for w in [
            "charging", "chraging", "chargin", "chagring", "chargign",
            "battery", "charge", "chrg", "battry", "bettery"
        ])
        is_charge_indicator = any(c in clean_no_punct for c in [
            "percent", "percentage", "%", "level", "status", "how",
            "what", "much", "life", "now", "current", "state", "is it", "is laptop"
        ])
        if (
            (is_charge_word and is_charge_indicator)
            or clean_no_punct in ["battery", "charging", "charge", "chraging", "battery status", "charge status"]
            or "percentage of" in clean_no_punct and is_charge_word
        ):
            return {"intent": "SYSTEM_INFO", "raw_text": raw, "params": {"metric": "battery"}}

        if any(w in clean for w in ["system status", "system info", "diagnostics", "computer status"]):
            return {"intent": "SYSTEM_INFO", "raw_text": raw, "params": {"metric": "all"}}

        # Date & Time Queries (Native Real-Time Clock)
        clean_no_punct = clean.rstrip("?.! ")
        time_patterns = [
            "what is the time", "what's the time", "whats the time", "what is time", "tell me the time",
            "what time is it", "what time is it now", "tell me time", "current time", "time now",
            "exact time", "what time", "what is current time"
        ]
        date_patterns = [
            "what is the date today", "what date is today", "what's the date today", "whats the date today",
            "what is today date", "date today", "today date", "tell me the date today", "tell me the date",
            "tell me today's date", "tell today date", "what date is it", "what is date today",
            "what is the date", "what's the date", "whats the date", "what is today's date",
            "what's today's date", "whats todays date", "today's date", "todays date", "current date",
            "what is current date", "exact date", "what date is"
        ]
        datetime_patterns = [
            "date and time", "time and date", "what is the date and time", "what is the time and date",
            "tell me the date and time", "current date and time", "exact date and time"
        ]

        is_date_regex = (
            bool(re.search(r"\b(?:what(?:'s|s| is)?|tell me)?\s*(?:the\s+)?(?:current\s+)?date\s*(?:is\s+it\s*)?(?:today)?\b", clean_no_punct))
            or bool(re.search(r"\bwhat\s+date\s+is\s+(?:it\s+)?today\b", clean_no_punct))
            or bool(re.search(r"\b(?:tell|what is)\s+(?:today\s+)?date\b", clean_no_punct))
        )

        if any(p in clean_no_punct for p in datetime_patterns):
            return {"intent": "GET_DATE_TIME", "raw_text": raw, "params": {"type": "both"}}
        if any(p in clean_no_punct for p in time_patterns) or clean_no_punct == "time":
            return {"intent": "GET_DATE_TIME", "raw_text": raw, "params": {"type": "time"}}
        if any(p in clean_no_punct for p in date_patterns) or clean_no_punct in ["date", "date today", "today date"] or is_date_regex:
            return {"intent": "GET_DATE_TIME", "raw_text": raw, "params": {"type": "date"}}

        # Wi-Fi Control (Native Radio Control - handles "turn one wifi", "turn on wifi", etc.)
        # Toggle: bare "turn wifi" / "turn wi-fi" (no on/off qualifier) → auto-detect state and flip
        wifi_toggle_patterns = [
            "turn wifi", "turn wi-fi", "toggle wifi", "toggle wi-fi"
        ]
        wifi_on_patterns = [
            "turn on wifi", "turn one wifi", "turn 1 wifi", "turn on the wifi", "turn one the wifi", "turn 1 the wifi",
            "turn on wi-fi", "turn one wi-fi", "turn 1 wi-fi", "turn on the wi-fi", "turn one the wi-fi",
            "enable wifi", "enable wi-fi", "switch on wifi", "switch one wifi", "switch on wi-fi", "switch one wi-fi",
            "wifi on", "wifi one", "wifi 1", "wi-fi on", "wi-fi one", "turn wifi on", "turn wifi one", "turn wi-fi on", "turn wi-fi one",
            "connect wifi", "start wifi", "wifi turn on", "wifi turn one", "wi-fi turn on", "wi-fi turn one"
        ]
        wifi_off_patterns = [
            "turn off wifi", "turn of wifi", "turn off the wifi", "turn of the wifi",
            "turn off wi-fi", "turn of wi-fi", "turn off the wi-fi", "turn of the wi-fi",
            "disable wifi", "disable wi-fi", "switch off wifi", "switch off wi-fi",
            "wifi off", "wi-fi off", "turn wifi off", "turn wi-fi off", "disconnect wifi", "stop wifi",
            "wifi turn off", "wi-fi turn off"
        ]
        wifi_status_patterns = [
            "wifi status", "wi-fi status", "is wifi on", "is wi-fi on", "check wifi", "check wi-fi"
        ]

        is_wifi_on = (
            any(w in clean_no_punct for w in wifi_on_patterns)
            or bool(re.search(r"\b(?:turn|switch)\s+(?:on|one|1)\s+(?:the\s+)?wi[- ]?fi\b", clean_no_punct))
            or bool(re.search(r"\bwi[- ]?fi\s+(?:turn\s+)?(?:on|one|1)\b", clean_no_punct))
        )
        is_wifi_off = (
            any(w in clean_no_punct for w in wifi_off_patterns)
            or bool(re.search(r"\b(?:turn|switch)\s+(?:off|of)\s+(?:the\s+)?wi[- ]?fi\b", clean_no_punct))
            or bool(re.search(r"\bwi[- ]?fi\s+(?:turn\s+)?(?:off|of)\b", clean_no_punct))
        )
        # Bare toggle: must match exactly and not overlap with on/off patterns
        is_wifi_toggle = (
            not is_wifi_on and not is_wifi_off
            and any(clean_no_punct == w or clean_no_punct.endswith(" " + w) for w in wifi_toggle_patterns)
        )

        if is_wifi_toggle:
            return {"intent": "WIFI_CONTROL", "raw_text": raw, "params": {"action": "toggle"}}
        if is_wifi_on and not is_wifi_off:
            return {"intent": "WIFI_CONTROL", "raw_text": raw, "params": {"action": "on"}}
        if is_wifi_off:
            return {"intent": "WIFI_CONTROL", "raw_text": raw, "params": {"action": "off"}}
        if any(w in clean_no_punct for w in wifi_status_patterns):
            return {"intent": "WIFI_CONTROL", "raw_text": raw, "params": {"action": "status"}}

        # Bluetooth Control (Native Radio Control - handles "turn on bluetooth", "turn one bluetooth", etc.)
        # Toggle: bare "turn bluetooth" (no on/off qualifier) → auto-detect state and flip
        bt_toggle_patterns = [
            "turn bluetooth", "toggle bluetooth"
        ]
        bt_on_patterns = [
            "turn on bluetooth", "turn one bluetooth", "turn 1 bluetooth",
            "turn on the bluetooth", "turn one the bluetooth", "enable bluetooth",
            "switch on bluetooth", "switch one bluetooth", "switch on the bluetooth",
            "bluetooth on", "bluetooth one", "turn bluetooth on", "turn bluetooth one",
            "start bluetooth", "connect bluetooth", "bluetooth turn on", "bluetooth turn one"
        ]
        bt_off_patterns = [
            "turn off bluetooth", "turn of bluetooth", "turn off the bluetooth", "turn of the bluetooth",
            "disable bluetooth", "switch off bluetooth", "switch of bluetooth",
            "bluetooth off", "turn bluetooth off", "stop bluetooth", "disconnect bluetooth",
            "bluetooth turn off"
        ]
        bt_status_patterns = [
            "bluetooth status", "is bluetooth on", "check bluetooth"
        ]

        is_bt_on = (
            any(w in clean_no_punct for w in bt_on_patterns)
            or bool(re.search(r"\b(?:turn|switch)\s+(?:on|one|1)\s+(?:the\s+)?bluetooth\b", clean_no_punct))
            or bool(re.search(r"\bbluetooth\s+(?:turn\s+)?(?:on|one|1)\b", clean_no_punct))
        )
        is_bt_off = (
            any(w in clean_no_punct for w in bt_off_patterns)
            or bool(re.search(r"\b(?:turn|switch)\s+(?:off|of)\s+(?:the\s+)?bluetooth\b", clean_no_punct))
            or bool(re.search(r"\bbluetooth\s+(?:turn\s+)?(?:off|of)\b", clean_no_punct))
        )
        # Bare toggle: must match exactly and not overlap with on/off patterns
        is_bt_toggle = (
            not is_bt_on and not is_bt_off
            and any(clean_no_punct == w or clean_no_punct.endswith(" " + w) for w in bt_toggle_patterns)
        )

        if is_bt_toggle:
            return {"intent": "BLUETOOTH_CONTROL", "raw_text": raw, "params": {"action": "toggle"}}
        if is_bt_on and not is_bt_off:
            return {"intent": "BLUETOOTH_CONTROL", "raw_text": raw, "params": {"action": "on"}}
        if is_bt_off:
            return {"intent": "BLUETOOTH_CONTROL", "raw_text": raw, "params": {"action": "off"}}
        if any(w in clean_no_punct for w in bt_status_patterns):
            return {"intent": "BLUETOOTH_CONTROL", "raw_text": raw, "params": {"action": "status"}}

        # Airplane / Aeroplane Mode Control
        airplane_on_patterns = [
            "turn on airplane mode", "turn on aeroplane mode", "turn on areplane mode", "turn on aeroplaane mode",
            "airplane mode on", "aeroplane mode on", "areplane mode on", "aeroplaane mode on",
            "enable airplane mode", "enable aeroplane mode", "enable areplane mode",
            "switch on airplane mode", "switch on aeroplane mode", "activate airplane mode", "activate aeroplane mode",
            "turn airplane mode on", "turn aeroplane mode on", "start airplane mode"
        ]
        airplane_off_patterns = [
            "turn off airplane mode", "turn off aeroplane mode", "turn off areplane mode", "turn off aeroplaane mode",
            "airplane mode off", "aeroplane mode off", "areplane mode off", "aeroplaane mode off",
            "disable airplane mode", "disable aeroplane mode", "disable areplane mode",
            "switch off airplane mode", "switch off aeroplane mode", "deactivate airplane mode", "deactivate aeroplane mode",
            "turn airplane mode off", "turn aeroplane mode off", "stop airplane mode"
        ]
        airplane_status_patterns = [
            "airplane mode status", "aeroplane mode status", "is airplane mode on", "is aeroplane mode on",
            "check airplane mode", "check aeroplane mode"
        ]
        if any(w in clean_no_punct for w in airplane_on_patterns) or clean_no_punct in ["airplane on", "aeroplane on", "areplane on", "aeroplaane on"]:
            return {"intent": "AIRPLANE_MODE_CONTROL", "raw_text": raw, "params": {"action": "on"}}
        if any(w in clean_no_punct for w in airplane_off_patterns) or clean_no_punct in ["airplane off", "aeroplane off", "areplane off", "aeroplaane off"]:
            return {"intent": "AIRPLANE_MODE_CONTROL", "raw_text": raw, "params": {"action": "off"}}
        if any(w in clean_no_punct for w in airplane_status_patterns):
            return {"intent": "AIRPLANE_MODE_CONTROL", "raw_text": raw, "params": {"action": "status"}}

        # Brightness Control
        bright_words = ["brightness", "brigthness", "brigtness", "brightnes", "screen light", "display brightness"]
        is_bright = any(bw in clean_no_punct for bw in bright_words) or any(clean_no_punct == w for w in ["brighter", "dimmer", "dim screen"])
        if is_bright:
            # Check percentage set: "set brightness to 80%", "set brightness to 50", "brightness 70%"
            m_set = re.search(r"(?:set\s+)?(?:the\s+)?(?:brightness|brigthness|brigtness|screen light)\s+(?:to\s+)?(\d+)\s*%?", clean_no_punct)
            if not m_set:
                m_set = re.search(r"(\d+)\s*%\s*(?:brightness|brigthness)", clean_no_punct)
            if m_set:
                lvl = int(m_set.group(1))
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "set", "level": lvl}}

            # Check max / min
            if any(w in clean_no_punct for w in ["max", "maximum", "full", "highest", "100%"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "max"}}
            if any(w in clean_no_punct for w in ["min", "minimum", "lowest", "least"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "min"}}

            # Check check / status
            if any(w in clean_no_punct for w in ["status", "check", "what is", "how much", "current", "level"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "status"}}

            # Check increase / up / more / boost
            if any(w in clean_no_punct for w in ["increase", "increse", "up", "more", "raise", "boost", "turn up", "make brighter", "higher"]):
                m_step = re.search(r"by\s+(\d+)", clean_no_punct)
                step = int(m_step.group(1)) if m_step else 15
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "up", "level": step}}

            # Check decrease / down / less / dim
            if any(w in clean_no_punct for w in ["decrease", "decrese", "down", "less", "lower", "reduce", "dim", "dimmer", "turn down", "make dimmer"]):
                m_step = re.search(r"by\s+(\d+)", clean_no_punct)
                step = int(m_step.group(1)) if m_step else 15
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "down", "level": step}}

            # Default if user just said "brighter" or "dimmer"
            if "brighter" in clean_no_punct:
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "up", "level": 15}}
            if "dimmer" in clean_no_punct or "dim" in clean_no_punct:
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw, "params": {"action": "down", "level": 15}}

        # Accessibility Control (Magnifier, Narrator, On-Screen Keyboard, High Contrast)
        if any(w in clean_no_punct for w in ["magnifier", "magnify"]):
            act = "off" if any(w in clean_no_punct for w in ["off", "close", "stop", "disable", "shut"]) else "on"
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw, "params": {"action": act, "feature": "magnifier"}}

        if any(w in clean_no_punct for w in ["narrator"]):
            act = "off" if any(w in clean_no_punct for w in ["off", "close", "stop", "disable", "shut"]) else "on"
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw, "params": {"action": act, "feature": "narrator"}}

        if any(w in clean_no_punct for w in ["on screen keyboard", "on-screen keyboard", "osk", "virtual keyboard"]):
            act = "off" if any(w in clean_no_punct for w in ["off", "close", "stop", "disable", "shut"]) else "on"
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw, "params": {"action": act, "feature": "keyboard"}}

        if any(w in clean_no_punct for w in ["high contrast", "contrast mode"]):
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw, "params": {"action": "open", "feature": "highcontrast"}}

        if any(w in clean_no_punct for w in [
            "accessibility settings", "open accessibility", "accessibility",
            "ease of access settings", "open ease of access", "ease of access", "easeofaccess"
        ]):
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw, "params": {"action": "open", "feature": "general"}}

        # Windows Settings Pages
        settings_page_map = {
            "display settings": "display",
            "screen settings": "display",
            "sound settings": "sound",
            "audio settings": "sound",
            "volume settings": "sound",
            "wifi settings": "wifi",
            "wi-fi settings": "wifi",
            "network settings": "wifi",
            "bluetooth settings": "bluetooth",
            "airplane mode settings": "airplane",
            "aeroplane mode settings": "airplane",
            "battery settings": "battery",
            "power settings": "battery",
        }
        for phrase, target_page in settings_page_map.items():
            if phrase in clean_no_punct or f"open {phrase}" in clean_no_punct:
                return {"intent": "OPEN_SETTINGS", "raw_text": raw, "params": {"setting": target_page}}

        settings_general_triggers = [
            "settings", "setting", "open settings", "open setting", "open the settings", "open my settings",
            "windows settings", "open windows settings", "settings app", "open settings app",
            "pc settings", "open pc settings", "system settings", "open system settings",
            "laptop settings", "open laptop settings",
            # Acoustic and phonetic variants of 'open settings' from speech recognition
            "all been sitting", "all been setting", "open sitting", "open sittings",
            "sitting", "sittings", "all been seated", "open seated"
        ]
        if (
            clean_no_punct in settings_general_triggers
            or any(clean_no_punct == t for t in settings_general_triggers)
            or any(clean_no_punct.startswith(f"open {t}") for t in ["settings", "setting", "sittings", "sitting"])
            or any(t == clean_no_punct.replace("the ", "").replace("my ", "").strip() for t in settings_general_triggers)
            or (("open" in clean_no_punct or "launch" in clean_no_punct) and any(w in clean_no_punct for w in ["setting", "settings", "sitting", "sittings"]))
        ):
            return {"intent": "OPEN_SETTINGS", "raw_text": raw, "params": {"setting": "general"}}

        # Volume Control
        if any(w in clean_no_punct for w in ["volume max", "max volume", "maximum volume", "full volume", "volume 100"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "max"}}
        if any(w in clean_no_punct for w in ["volume min", "min volume", "minimum volume", "lowest volume"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "min"}}
        if any(w in clean_no_punct for w in ["volume up", "increase volume", "turn up volume", "raise volume", "louder", "make it louder"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "up"}}
        if any(w in clean_no_punct for w in ["volume down", "decrease volume", "lower volume", "turn down volume", "quieter", "make it quieter"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "down"}}
        if "unmute" in clean_no_punct or "un-mute" in clean_no_punct:
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "unmute"}}
        if clean_no_punct == "mute" or "mute audio" in clean_no_punct or "mute volume" in clean_no_punct:
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "mute"}}
        vol_match = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)\s*%?", clean_no_punct)
        if vol_match:
            return {"intent": "VOLUME_CONTROL", "raw_text": raw, "params": {"action": "set", "level": int(vol_match.group(1))}}


        # 6. Multi-Step In-App Task Planning
        # Deconstructs compound, in-app, or chained actions (e.g. WhatsApp messaging,
        # Chrome search + open first result, Spotify playback, Calculator math, etc.)
        planned_task = task_planner.plan(raw)
        if planned_task:
            logger.info(f"Task planner generated plan {planned_task.plan_id} with {len(planned_task.steps)} steps for query: '{raw}'")
            return {
                "intent": "EXECUTE_TASK_PLAN",
                "raw_text": raw,
                "params": {"plan": planned_task}
            }

        # 7. Developer Mode: Compile and Run / Compile / Run / Explain
        # "compile and run X"
        m_compile_run = re.search(r"compile and run\s+([a-zA-Z0-9_\-\.]+)", raw, re.IGNORECASE)
        if m_compile_run:
            file_name = m_compile_run.group(1).strip()
            return {"intent": "COMPILE_AND_RUN_CODE", "raw_text": raw, "params": {"file_name": file_name}}

        # "compile X" or "compile it"
        m_compile = re.search(r"compile\s+([a-zA-Z0-9_\-\.]+)", raw, re.IGNORECASE)
        if m_compile:
            file_name = m_compile.group(1).strip()
            params = conversation_context.resolve_reference(raw, {"file_name": file_name if file_name.lower() != "it" else None})
            return {"intent": "COMPILE_CODE", "raw_text": raw, "params": params}

        # "run X" or "run it" or "execute X"
        m_run = re.search(r"(?:run|execute)\s+([a-zA-Z0-9_\-\.]+)", raw, re.IGNORECASE)
        if m_run and not any(w in clean for w in ["chrome", "vscode", "vs code", "discord"]):
            file_name = m_run.group(1).strip()
            params = conversation_context.resolve_reference(raw, {"file_name": file_name if file_name.lower() != "it" else None})
            return {"intent": "RUN_CODE", "raw_text": raw, "params": params}

        # "explain the error", "explain error"
        if any(w in clean for w in ["explain the error", "explain error", "what is the error", "what caused the error"]):
            return {"intent": "EXPLAIN_ERROR", "raw_text": raw, "params": {}}

        # 7. Web Navigation & Search
        # "open youtube in chrome"
        m_web_browser = re.search(r"open\s+(.+?)\s+in\s+([a-zA-Z0-9_\-]+)", raw, re.IGNORECASE)
        if m_web_browser:
            site = m_web_browser.group(1).strip()
            browser = m_web_browser.group(2).strip()
            return {"intent": "OPEN_WEBSITE", "raw_text": raw, "params": {"website": site, "browser": browser}}

        # "search youtube for X"
        m_search_yt = re.search(r"^(?:please\s+)?(?:can you\s+)?search\s+(?:on\s+|in\s+)?youtube\s+(?:for\s+)?(.+)", raw, re.IGNORECASE)
        if m_search_yt:
            return {"intent": "SEARCH_WEB", "raw_text": raw, "params": {"query": m_search_yt.group(1).strip(), "engine": "youtube"}}

        # "search google for X" / "search on google for X" / "search web for X"
        m_search_web = re.search(r"^(?:please\s+)?(?:can you\s+)?search\s+(?:on\s+|in\s+)?(?:google|web|online|bing)\s+(?:for\s+)?(.+)", raw, re.IGNORECASE)
        if m_search_web and not any(w in clean for w in ["files", "file", "drive", "youtube"]):
            return {"intent": "SEARCH_WEB", "raw_text": raw, "params": {"query": m_search_web.group(1).strip(), "engine": "google"}}

        # File search routing
        m_find_file = re.search(r"^(?:please\s+)?(?:can you\s+)?(?:find\s+file|search\s+(?:for\s+)?file[s]?|search\s+(?:in\s+)?(?:my\s+)?files)\s+(.+)", raw, re.IGNORECASE)
        if m_find_file:
            return {"intent": "SEARCH_FILES", "raw_text": raw, "params": {"pattern": m_find_file.group(1).strip()}}

        # ── EXPLICIT SEARCH COMMAND ──────────────────────────────────────────────
        # When command starts with "search", remove command word "search" and use everything after it as the Google search query.
        # Routes DIRECTLY to SEARCH_WEB (Chrome → Google). Never to ASK_AI.
        # Dedicated search intent triggered by: "Hey Doom, search [query]" or typed: "search [query]"
        m_explicit_search = re.match(
            r"^(?:please\s+)?(?:can\s+you\s+)?search\b\s*(.*)",
            raw,
            re.IGNORECASE
        )
        if m_explicit_search and not any(clean.startswith(w) for w in ["search files", "search file", "search in files", "search for file", "search youtube", "search on youtube", "search in youtube"]):
            # Remove the command word "search" and use everything after it as the search query
            q = m_explicit_search.group(1).strip()
            # If phrased as "search for X", strip leading "for " unless query is e.g. "for loop"
            if q.lower().startswith("for ") and not q.lower().startswith("for loop"):
                q_candidate = q[4:].strip()
                if q_candidate:
                    q = q_candidate
            elif q.lower().startswith("about "):
                q_candidate = q[6:].strip()
                if q_candidate:
                    q = q_candidate
            q_clean = q.strip("?.! ")

            # Contextual pronoun resolution ("search that", "search it", "search this")
            if not q_clean or q_clean.lower() in ["that", "it", "this", "about that", "about it", "about this"]:
                resolved_params = conversation_context.resolve_reference(raw, {"query": q_clean})
                q_resolved = resolved_params.get("query", "")
                if q_resolved and q_resolved.lower() not in ["that", "it", "this", "about that", "about it", "about this"]:
                    q_clean = q_resolved
                elif conversation_context.last_topic:
                    q_clean = conversation_context.last_topic
                elif conversation_context.last_query:
                    q_clean = conversation_context.last_query
                elif conversation_context.current_app:
                    q_clean = f"{conversation_context.current_app} information"
                else:
                    q_clean = "DOOM AI"

            conversation_context.update(last_query=q_clean, last_topic=q_clean)
            return {"intent": "SEARCH_WEB", "raw_text": raw, "params": {"query": q_clean, "engine": "google"}}

        # Email & Gmail commands (opens Chrome with default profile moniswarmoni509@gmail.com)
        email_phrases = [
            "open email", "open my email", "check email", "check my email",
            "open mail", "check mail", "open my mail", "open gmail", "check gmail",
            "open inbox", "check inbox", "my email", "gmail", "inbox"
        ]
        if any(w in clean for w in email_phrases) or clean in ["email", "gmail", "mail"]:
            return {"intent": "OPEN_WEBSITE", "raw_text": raw, "params": {"website": "gmail", "browser": "chrome"}}

        # Common websites directly: "open github", "open youtube", "open google"
        common_sites = ["youtube", "github", "google", "gmail", "reddit", "stackoverflow", "chatgpt"]
        for site in common_sites:
            if re.search(rf"\bopen\s+{site}\b", clean) and not any(w in clean for w in ["chrome", "app", "browser", "application"]):
                return {"intent": "OPEN_WEBSITE", "raw_text": raw, "params": {"website": site, "browser": "chrome"}}

        # 8. Application Close (Checked before Open to prevent collisions)
        clean_no_punct = clean.rstrip("?.! ")
        # Normalize phonetic close aliases (clothes -> close, closed -> close, cloze -> close, sitting -> settings)
        clean_no_punct = re.sub(r"\b(?:clothes|closed|cloze)\b", "close", clean_no_punct)
        clean_no_punct = re.sub(r"\bclose\s+(?:sitting|sittings)\b", "close settings", clean_no_punct)

        # Explicit Settings Close
        if clean_no_punct in [
            "close settings", "close setting", "close the settings", "close my settings",
            "close windows settings", "close pc settings", "close system settings", "close laptop settings",
            "settings close", "setting close", "windows settings close", "close sitting", "close sittings",
            "settings close chey", "settings close cheyyi"
        ]:
            return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "settings"}}

        # Reverse syntax: e.g. "whatsapp close", "settings close", "chrome close", "window close"
        m_reverse = re.match(r"^([a-zA-Z0-9_\s\-\.]+?)\s+(?:close|quit|exit|terminate|kill|shut down|stop|close chey|close cheyyi)$", clean_no_punct)
        if m_reverse:
            t = m_reverse.group(1).strip()
            if t in ["window", "the window", "this window", "app", "the app", "it", "this"]:
                params = conversation_context.resolve_reference(raw, {"app_name": "active"})
                return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": params}
            elif t in ["all", "all apps", "all windows", "everything"]:
                return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "all"}}
            elif t in ["tab", "the tab"]:
                return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "tab"}}
            elif t in ["settings", "setting", "windows settings", "pc settings"]:
                return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "settings"}}
            else:
                return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": t}}

        # 8a. Close All Apps / Everything
        close_all_phrases = [
            "close all apps", "close all applications", "close all windows", "close all programs",
            "close all tabs", "close all", "close apps", "close everything", "quit all", "exit all",
            "close all app", "close app for apps", "close all app for apps"
        ]
        if clean_no_punct in close_all_phrases:
            return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "all"}}

        # 8b. Close Tab
        close_tab_phrases = [
            "close tab", "close the tab", "close this tab", "close current tab", "close active tab",
            "close browser tab", "close window tab"
        ]
        if clean_no_punct in close_tab_phrases:
            return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "tab"}}

        # 8c. Close File Explorer / Folder Windows
        close_explorer_phrases = [
            "close file explorer", "close explorer",
            "close folder", "close folders", "close directory", "close file manager",
            "close this pc", "close my computer", "close downloads folder",
            "close downloads", "close documents folder", "close documents", "close explore"
        ]
        if clean_no_punct in close_explorer_phrases or any(clean_no_punct.startswith(p) for p in [
            "close file explorer", "close explorer", "close folder", "close explore"
        ]):
            return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "file explorer"}}

        # 8d. Standalone / Active / Generic Close ("close", "close app", "close this", "close window", "close it", etc.)
        generic_close_phrases = [
            "close", "quit", "exit", "close it", "close this", "close that", "close app", "close the app",
            "close this app", "close current app", "close active app", "close application", "close the application",
            "close this application", "close window", "close the window", "close this window", "close current window",
            "close active window", "close program", "close the program", "close this program", "stop it",
            "quit app", "quit this app", "exit app", "exit this app", "exit window", "terminate app"
        ]
        if clean_no_punct in generic_close_phrases:
            params = conversation_context.resolve_reference(raw, {"app_name": "active"})
            return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": params}

        # 8e. Close Specific Application or Website
        close_patterns = [
            r"^(?:please\s+)?(?:can you\s+)?(?:close|quit|exit|terminate|kill|shut down|stop)\s+(?:the\s+|my\s+)?(?:application\s+|app\s+|window\s+|program\s+)?([a-zA-Z0-9_\s\-\.]+)",
            r"\b(?:close|quit|exit|terminate|kill)\s+(?:the\s+|my\s+)?(?:application\s+|app\s+|window\s+|program\s+)?([a-zA-Z0-9_\s\-\.]+)",
        ]
        for pat in close_patterns:
            m_close_app = re.search(pat, raw, re.IGNORECASE)
            if m_close_app:
                target = m_close_app.group(1).strip()
                target_clean = target.lower()
                for prefix in ["the ", "my ", "an ", "a ", "app ", "application ", "window ", "program "]:
                    if target_clean.startswith(prefix):
                        target_clean = target_clean[len(prefix):].strip()
                for suffix in [" please", " application", " app", " window", " program", " now", " for me", " tabs", " tab"]:
                    if target_clean.endswith(suffix):
                        target_clean = target_clean[:-len(suffix)].strip()
                
                if not target_clean or target_clean in ["it", "this", "that", "app", "application", "window", "current", "active"]:
                    params = conversation_context.resolve_reference(raw, {"app_name": "active"})
                    return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": params}
                elif target_clean in ["all", "all apps", "all applications", "all windows", "apps", "everything", "app for apps"]:
                    return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "all"}}
                elif target_clean in ["tab", "current tab"]:
                    return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "tab"}}
                elif target_clean in [
                    "my file", "my files", "the file", "the files",
                    "file explorer", "the file explorer", "the file explore",
                    "explorer", "folder", "folders", "directory", "directories",
                    "this pc", "my computer", "computer", "file manager", "downloads", "documents"
                ]:
                    return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": "file explorer"}}
                elif not any(target_clean.endswith(ext) for ext in [".java", ".py", ".c", ".cpp", ".js", ".html", ".txt"]):
                    return {"intent": "CLOSE_APPLICATION", "raw_text": raw, "params": {"app_name": target_clean}}

        # 9. File Operations & Explorer (Requires explicit open verb)
        downloads_open_phrases = [
            "open downloads", "open download", "open my downloads", "open downloads folder",
            "show downloads", "show my downloads", "downloads folder"
        ]
        if any(clean == phrase or clean.startswith(phrase + " ") or f" {phrase}" in clean for phrase in downloads_open_phrases):
            return {"intent": "OPEN_FILE", "raw_text": raw, "params": {"file_path": "Downloads", "is_folder": True}}

        explorer_open_phrases = [
            "open file explorer", "open file explore", "open explorer", "open explore",
            "open my files", "open files", "show files", "show my files",
            "open file manager", "open folder", "open directory", "open this pc"
        ]
        if any(w in clean for w in explorer_open_phrases) and not any(w in clean for w in ["close", "exit", "quit", "kill", "terminate", "stop"]):
            return {"intent": "OPEN_APPLICATION", "raw_text": raw, "params": {"app_name": "file explorer"}}

        m_create_file = re.search(r"create\s+(?:file\s+)?([a-zA-Z0-9_\-\.]+)", raw, re.IGNORECASE)
        if m_create_file and not any(w in clean for w in ["voice profile", "profile"]):
            return {"intent": "CREATE_FILE", "raw_text": raw, "params": {"file_name": m_create_file.group(1).strip()}}

        m_delete_file = re.search(r"delete\s+(?:file\s+)?([a-zA-Z0-9_\-\.]+)", raw, re.IGNORECASE)
        if m_delete_file:
            return {"intent": "DELETE_FILE", "raw_text": raw, "params": {"file_name": m_delete_file.group(1).strip()}}

        # Explicit web resource & information search patterns
        m_web_info = re.search(r"^(?:find|search for|search|lookup|look up)\s+(?:information|info|details)\s+(?:about|on|regarding)\s+(.+)", raw, re.IGNORECASE)
        if m_web_info:
            return {"intent": "SEARCH_WEB", "raw_text": raw, "params": {"query": m_web_info.group(1).strip()}}

        m_web_site = re.search(r"^(?:find|search for|search|open|show)\s+(?:the\s+)?(?:official\s+)?website\s+(?:of|for)\s+(.+)", raw, re.IGNORECASE)
        if m_web_site:
            return {"intent": "SEARCH_WEB", "raw_text": raw, "params": {"query": f"{m_web_site.group(1).strip()} official website"}}

        m_find_file = re.search(r"(?:find|search for file|search file)\s+(.+)", raw, re.IGNORECASE)
        if m_find_file:
            return {"intent": "SEARCH_FILES", "raw_text": raw, "params": {"pattern": m_find_file.group(1).strip()}}

        app_patterns = [
            r"^(?:can you\s+)?(?:open|launch|start)\s+([a-zA-Z0-9_\s\-\.]+)",
            r"^i need\s+([a-zA-Z0-9_\s\-\.]+)"
        ]
        for pat in app_patterns:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                target = m.group(1).strip()
                if any(target.lower().endswith(ext) for ext in [".java", ".py", ".c", ".cpp", ".js", ".html", ".txt", ".json"]):
                    return {"intent": "OPEN_FILE", "raw_text": raw, "params": {"file_name": target}}
                return {"intent": "OPEN_APPLICATION", "raw_text": raw, "params": {"app_name": target}}

        # Ambient noise and stopword fragments filter
        noise_fragments = [
            "at the", "in the", "on the", "to the", "of the", "for the", "and the", "with the",
            "is the", "it the", "that the", "all the"
        ]
        if clean in noise_fragments:
            return {
                "intent": "UNKNOWN",
                "raw_text": raw,
                "params": {"query": raw}
            }

        # Final check: does this look like a question or informational query? Route to ASK_AI.
        if cls._is_question(clean) or (len(clean.split()) >= 3 and clean not in noise_fragments):
            return {
                "intent": "ASK_AI",
                "raw_text": raw,
                "params": {"query": raw}
            }

        return {
            "intent": "UNKNOWN",
            "raw_text": raw,
            "params": {"query": raw}
        }

    @staticmethod
    def _is_question(text: str) -> bool:
        """Returns True if the text looks like a question or informational query."""
        # Ends with question mark
        if text.rstrip().endswith("?"):
            return True
        # Starts with a recognised question trigger word
        for prefix in _QUESTION_PREFIXES:
            if text.startswith(prefix):
                return True
        # Contains code or conceptual knowledge doubt keywords
        knowledge_doubt_keywords = [
            "error", "exception", "bug", "crash", "fix", "problem",
            "syntax", "debug", "traceback", "undefined", "null pointer",
            "segfault", "memory leak", "algorithm", "data structure",
            "review", "reviews", "search", "google", "movie", "film",
            "meaning", "definition", "concept", "history", "advantages",
            "disadvantages", "difference", "comparison", "tutorial", "guide",
            "quantum", "operating system", "machine learning", "turbocharger"
        ]
        return any(kw in text for kw in knowledge_doubt_keywords)

