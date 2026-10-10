"""
VIKRAM / DOOM AI - Native Telugu Language & Tanglish Intelligence Core
Strict Bilingual System (1. English, 2. Telugu).
Handles:
1. Telugu Unicode script detection (\\u0C00-\\u0C7F) & Tanglish transliterated roman script detection.
2. Telugu command parsing into structured system intents.
3. Natural, polite, human Telugu voice response generation addressing the user as 'మాస్టర్'.
"""

import logging
import re
from typing import Any

logger = logging.getLogger("vikram.ai.telugu")

# Common English/Telugu app name translation dictionary
APP_NAME_MAP = {
    "వాట్సాప్": "whatsapp",
    "వాట్సప్": "whatsapp",
    "క్రోమ్": "chrome",
    "గూగుల్ క్రోమ్": "chrome",
    "సెట్టింగ్స్": "settings",
    "సెట్టింగులు": "settings",
    "క్యాలిక్యులేటర్": "calculator",
    "ఫైల్ ఎక్స్‌ప్లోరర్": "file explorer",
    "ఫైల్స్": "file explorer",
    "ఫైల్": "file explorer",
    "యూట్యూబ్": "youtube",
    "స్పాటిఫై": "spotify",
    "నోట్‌ప్యాడ్": "notepad",
    "విఎస్‌కోడ్": "vscode",
    "విఎస్ కోడ్": "vscode",
    "బ్రౌజర్": "chrome",
    "కెమెరా": "camera",
    "పెయింట్": "paint",
    "టాస్క్ మేనేజర్": "task manager",
    "టర్మినల్": "terminal",
}

# Tanglish verbal keywords and particles
TANGLISH_VERB_MARKERS = {
    "cheyyi", "chey", "cheyyara", "cheyyandi", "cheddam", "cheyali",
    "pettu", "pampu", "pampinchu", "pettuko",
    "penchu", "thagginchu", "tagginchu", "aapu", "apali", "apandi",
    "theruvu", "teruvu", "moosi", "moosiveyyi", "mosi", "veyyi",
    "kanipinchu", "chudu", "matladu", "cheppu", "kalupu", "lekkimchu", "lekkissu"
}

TANGLISH_QUESTION_MARKERS = {
    "entha", "enta", "enti", "emiti", "emi", "ela", "evaru", "ekkada",
    "eppudu", "epudu", "enduku", "endhuku", "unnava", "unnavu", "unnara",
    "undi", "undha", "cheppava", "cheppandi"
}

TANGLISH_PRONOUNS_PARTICLES = {
    "amma", "nanna", "thammudu", "anna", "akka", "chelli", "mithrama",
    "naaku", "naku", "neeku", "meeku", "mana", "manaki",
    "ani", "ki", "tho", "lo", "kosam", "gurinchi", "ippudu", "samayam",
    "eroju", "eeroju", "namaskaram", "namaste", "bagunnava", "bagunnanu"
}


def is_telugu_script(text: str) -> bool:
    """Returns True if the text contains Telugu Unicode characters."""
    if not text:
        return False
    return any("\u0C00" <= ch <= "\u0C7F" for ch in text)


def is_tanglish(text: str) -> bool:
    """Returns True if the text is phonetic transliterated Telugu (Tanglish)."""
    if not text:
        return False
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return False

    matches = 0
    for w in words:
        if w in TANGLISH_VERB_MARKERS or w in TANGLISH_QUESTION_MARKERS or w in TANGLISH_PRONOUNS_PARTICLES:
            matches += 1
        elif any(w.endswith(sfx) for sfx in ["cheyyi", "chey", "pettu", "pampu", "entha", "enti", "undi"]):
            matches += 1

    return matches >= 1


def is_telugu(text: str) -> bool:
    """Returns True if input is either Telugu script or Tanglish."""
    return is_telugu_script(text) or is_tanglish(text)


class TeluguEngine:
    @classmethod
    def parse_command(cls, raw_text: str) -> dict[str, Any] | None:
        """
        Parses a Telugu (script or Tanglish) command into an actionable intent.
        Returns None if not recognized as a Telugu structured command.
        """
        raw = raw_text.strip()
        if not raw:
            return None

        clean = raw.lower()

        # Strip Telugu wake words if present: "డూమ్", "హే డూమ్", "నమస్తే డూమ్", "hey doom", etc.
        wake_match = re.match(
            r"^(?:హే\s*డూమ్|డూమ్\s*ఏఐ|డూమ్|నమస్తే\s*డూమ్|నమస్కారం\s*డూమ్|ఓయ్\s*డూమ్|hey\s*doom|hi\s*doom|doom\s*ai|doom)\s*[,:\-]?\s*",
            clean,
            re.IGNORECASE
        )
        if wake_match:
            clean = clean[wake_match.end():].strip()
            raw = raw[wake_match.end():].strip()

        # 1. Greetings & Pleasantries
        greetings = [
            "నమస్కారం", "నమస్తే", "హాయ్", "హలో", "ఎలా ఉన్నావు", "నువ్వు ఎవరు",
            "బాగున్నావా", "namaskaram", "namaste", "ela unnavu", "ela unnaru",
            "nuvvu evaru", "bagunnava", "bagunnara"
        ]
        if clean in greetings or any(clean == g for g in greetings):
            return {
                "intent": "GREETING",
                "raw_text": raw_text,
                "language": "te",
                "params": {"query": clean}
            }

        # 2. System Unlock / Lock
        # Lock: "ల్యాప్‌టాప్ లాక్ చెయ్యి", "లాక్ చెయ్యి", "laptop lock cheyyi", "screen lock chey"
        if any(w in clean for w in ["లాక్ చెయ్యి", "లాక్ చేయ్", "లాక్", "ల్యాప్‌టాప్ లాక్", "laptop lock cheyyi", "lock cheyyi", "lock chey", "laptop lock", "screen lock", "pc lock"]):
            if not any(w in clean for w in ["అన్‌లాక్", "unlock"]):
                return {
                    "intent": "LOCK_DEVICE",
                    "raw_text": raw_text,
                    "language": "te",
                    "params": {}
                }

        # Unlock: "అన్‌లాక్ చెయ్యి", "స్క్రీన్ తెరువు", "unlock cheyyi", "wake up"
        if any(w in clean for w in ["అన్‌లాక్ చెయ్యి", "అన్‌లాక్", "unlock cheyyi", "unlock chey", "screen unlock"]):
            return {
                "intent": "UNLOCK_DEVICE",
                "raw_text": raw_text,
                "language": "te",
                "params": {}
            }

        # Shutdown / Restart / Sleep
        if any(w in clean for w in ["షట్‌డౌన్ చెయ్యి", "ల్యాప్‌టాప్ ఆపు", "shutdown cheyyi", "laptop aapu", "turn off chey"]):
            return {"intent": "SHUTDOWN_DEVICE", "raw_text": raw_text, "language": "te", "params": {}}

        if any(w in clean for w in ["రీస్టార్ట్ చెయ్యి", "restart cheyyi", "reboot cheyyi"]):
            return {"intent": "RESTART_DEVICE", "raw_text": raw_text, "language": "te", "params": {}}

        if any(w in clean for w in ["స్లీప్ మోడ్", "స్లీప్ చెయ్యి", "sleep cheyyi", "sleep mode lo pettu"]):
            return {"intent": "SLEEP_DEVICE", "raw_text": raw_text, "language": "te", "params": {}}

        # 3. Time & Date Queries
        # "సమయం ఎంత", "టైమ్ ఎంత", "ఇప్పుడు టైమ్ ఎంత", "time entha", "samayam entha", "ippudu time entha"
        is_time = any(w in clean for w in ["సమయం ఎంత", "సమయం", "టైమ్ ఎంత", "టైం ఎంత", "time entha", "samayam entha", "ippudu time", "time enti"])
        is_date = any(w in clean for w in ["తేదీ ఎంత", "తేదీ ఏమిటి", "ఈరోజు తేదీ", "date entha", "date enti", "eroju date", "date cheppu"])

        if is_time and is_date:
            return {"intent": "GET_DATE_TIME", "raw_text": raw_text, "language": "te", "params": {"type": "both"}}
        if is_time:
            return {"intent": "GET_DATE_TIME", "raw_text": raw_text, "language": "te", "params": {"type": "time"}}
        if is_date:
            return {"intent": "GET_DATE_TIME", "raw_text": raw_text, "language": "te", "params": {"type": "date"}}

        # 4. Battery Telemetry
        # "బ్యాటరీ ఎంత ఉంది", "బ్యాటరీ ఎంత", "చార్జింగ్ ఎంత ఉంది", "battery entha", "battery entha undi", "charge entha"
        if any(w in clean for w in ["బ్యాటరీ", "ఛార్జింగ్", "చార్జింగ్", "battery", "charge", "charging"]) and any(w in clean for w in ["ఎంత", "శాతం", "entha", "percentage", "undi", "status"]):
            return {"intent": "SYSTEM_INFO", "raw_text": raw_text, "language": "te", "params": {"metric": "battery"}}

        # 5. Volume Control
        # Up: "వాల్యూమ్ పెంచు", "సౌండ్ పెంచు", "volume penchu", "sound penchu"
        if any(w in clean for w in ["వాల్యూమ్ పెంచు", "వాల్యుమ్ పెంచు", "సౌండ్ పెంచు", "volume penchu", "sound penchu", "volume ekkuva"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "up"}}

        # Down: "వాల్యూమ్ తగ్గించు", "సౌండ్ తగ్గించు", "volume thagginchu", "volume tagginchu", "sound thagginchu"
        if any(w in clean for w in ["వాల్యూమ్ తగ్గించు", "వాల్యుమ్ తగ్గించు", "సౌండ్ తగ్గించు", "volume thagginchu", "volume tagginchu", "sound tagginchu"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "down"}}

        # Mute / Unmute
        if any(w in clean for w in ["మ్యూట్ చెయ్యి", "మ్యూట్", "mute cheyyi", "mute chey"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "mute"}}
        if any(w in clean for w in ["అన్‌మ్యూట్ చెయ్యి", "అన్ మ్యూట్", "unmute cheyyi", "unmute chey"]):
            return {"intent": "VOLUME_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "unmute"}}

        # 6. Wi-Fi & Bluetooth Controls
        if any(w in clean for w in ["వైఫై ఆన్ చెయ్యి", "వైఫై ఆన్", "wifi on cheyyi", "wifi on chey"]):
            return {"intent": "WIFI_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "on"}}
        if any(w in clean for w in ["వైఫై ఆఫ్ చెయ్యి", "వైఫై ఆఫ్", "wifi off cheyyi", "wifi off chey"]):
            return {"intent": "WIFI_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "off"}}
        if any(w in clean for w in ["బ్లూటూత్ ఆన్ చెయ్యి", "బ్లూటూత్ ఆన్", "bluetooth on cheyyi", "bluetooth on chey"]):
            return {"intent": "BLUETOOTH_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "on"}}
        if any(w in clean for w in ["బ్లూటూత్ ఆఫ్ చెయ్యి", "బ్లూటూత్ ఆఫ్", "bluetooth off cheyyi", "bluetooth off chey"]):
            return {"intent": "BLUETOOTH_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "off"}}

        # 6b. Airplane / Aeroplane Mode Control
        if any(w in clean for w in [
            "ఏరోప్లేన్ మోడ్ ఆన్", "ఎయిర్‌ప్లేన్ మోడ్ ఆన్", "aeroplane mode on", "airplane mode on", "areplane mode on"
        ]):
            return {"intent": "AIRPLANE_MODE_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "on"}}
        if any(w in clean for w in [
            "ఏరోప్లేన్ మోడ్ ఆఫ్", "ఎయిర్‌ప్లేన్ మోడ్ ఆఫ్", "aeroplane mode off", "airplane mode off", "areplane mode off"
        ]):
            return {"intent": "AIRPLANE_MODE_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "off"}}
        if any(w in clean for w in [
            "ఏరోప్లేన్ మోడ్ స్టేటస్", "aeroplane mode status", "airplane mode status"
        ]):
            return {"intent": "AIRPLANE_MODE_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "status"}}

        # 6c. Brightness Control in Telugu / Tanglish
        if any(w in clean for w in ["బ్రైట్‌నెస్", "బ్రైట్ నెస్", "brightness", "brigthness"]):
            if any(w in clean for w in ["పెంచు", "ఎక్కువ", "penchu", "ekkuva", "up", "more"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "up", "level": 15}}
            if any(w in clean for w in ["తగ్గించు", "తక్కువ", "thagginchu", "tagginchu", "down", "less", "dim"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "down", "level": 15}}
            if any(w in clean for w in ["ఫుల్", "గరిష్ట", "full", "max"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "max"}}
            if any(w in clean for w in ["కనిష్ట", "min"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "min"}}
            m_lvl = re.search(r"(\d+)", clean)
            if m_lvl:
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "set", "level": int(m_lvl.group(1))}}
            if any(w in clean for w in ["ఎంత", "స్టేటస్", "entha", "status"]):
                return {"intent": "BRIGHTNESS_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "status"}}

        # 6d. Accessibility Controls in Telugu / Tanglish
        if any(w in clean for w in ["మాగ్నిఫైయర్", "magnifier", "magnify"]):
            act = "off" if any(w in clean for w in ["ఆపు", "ఆఫ్", "off", "close", "moosi"]) else "on"
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": act, "feature": "magnifier"}}

        if any(w in clean for w in ["నెరేటర్", "narrator"]):
            act = "off" if any(w in clean for w in ["ఆపు", "ఆఫ్", "off", "close", "moosi"]) else "on"
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": act, "feature": "narrator"}}

        if any(w in clean for w in ["ఆన్ స్క్రీన్ కీబోర్డ్", "on screen keyboard", "osk"]):
            act = "off" if any(w in clean for w in ["ఆపు", "ఆఫ్", "క్లోజ్", "off", "close", "moosi"]) else "on"
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": act, "feature": "keyboard"}}

        if any(w in clean for w in ["యాక్సెసిబిలిటీ", "accessibility"]):
            return {"intent": "ACCESSIBILITY_CONTROL", "raw_text": raw_text, "language": "te", "params": {"action": "open", "feature": "general"}}

        # 6e. Settings Pages in Telugu / Tanglish
        if any(w in clean for w in ["డిస్‌ప్లే సెట్టింగ్స్", "display settings"]):
            return {"intent": "OPEN_SETTINGS", "raw_text": raw_text, "language": "te", "params": {"setting": "display"}}
        if any(w in clean for w in ["సౌండ్ సెట్టింగ్స్", "sound settings"]):
            return {"intent": "OPEN_SETTINGS", "raw_text": raw_text, "language": "te", "params": {"setting": "sound"}}
        if any(w in clean for w in ["వైఫై సెట్టింగ్స్", "wifi settings"]):
            return {"intent": "OPEN_SETTINGS", "raw_text": raw_text, "language": "te", "params": {"setting": "wifi"}}
        if any(w in clean for w in ["బ్లూటూత్ సెట్టింగ్స్", "bluetooth settings"]):
            return {"intent": "OPEN_SETTINGS", "raw_text": raw_text, "language": "te", "params": {"setting": "bluetooth"}}
        if any(w in clean for w in ["సెట్టింగ్స్ ఓపెన్ చెయ్యి", "settings open cheyyi", "settings open chey"]):
            return {"intent": "OPEN_SETTINGS", "raw_text": raw_text, "language": "te", "params": {"setting": "general"}}

        # 7. Screenshot
        if any(w in clean for w in ["స్క్రీన్‌షాట్ తీయి", "స్క్రీన్ షాట్", "screenshot theeyi", "screenshot teeyi", "screenshot theesko"]):
            return {"intent": "SCREENSHOT", "raw_text": raw_text, "language": "te", "params": {}}

        # 8. WhatsApp Multi-Step Messaging in Telugu / Tanglish
        # Telugu script: "అమ్మకి హాయ్ అని మెసేజ్ పెట్టు", "వాట్సాప్ లో అమ్మకి హాయ్ అని మెసేజ్ పంపు"
        # Tanglish: "amma ki hi ani message pettu", "whatsapp lo amma ki hi ani message pampu"
        m_msg = cls._parse_telugu_whatsapp(raw, clean)
        if m_msg:
            return m_msg

        # 9. Application Close (Close checked before Open to prevent collision)
        # Telugu script: "వాట్సాప్ క్లోజ్ చెయ్యి", "సెట్టింగ్స్ మూసివెయ్యి", "యాప్స్ అన్నీ క్లోజ్ చెయ్యి"
        # Tanglish: "whatsapp close cheyyi", "settings close chey", "file explorer close cheyyi", "all apps close cheyyi"
        close_indicators = ["క్లోజ్ చెయ్యి", "క్లోజ్ చేయ్", "క్లోజ్", "మూసివెయ్యి", "మూసివేయి", "ఆపు", "close cheyyi", "close chey", "moosiveyyi", "moosi"]
        if any(ci in clean for ci in close_indicators):
            target_app = cls._extract_app_name(clean, is_close=True)
            if target_app:
                return {
                    "intent": "CLOSE_APPLICATION",
                    "raw_text": raw_text,
                    "language": "te",
                    "params": {"app_name": target_app}
                }

        # 10. Application Launch / Open
        # Telugu script: "వాట్సాప్ ఓపెన్ చెయ్యి", "సెట్టింగ్స్ ఓపెన్ చెయ్యి", "క్యాలిక్యులేటర్ తెరువు"
        # Tanglish: "whatsapp open cheyyi", "settings open chey", "chrome open cheyyi"
        open_indicators = ["ఓపెన్ చెయ్యి", "ఓపెన్ చేయ్", "ఓపెన్", "తెరువు", "స్టార్ట్ చెయ్యి", "open cheyyi", "open chey", "theruvu", "start cheyyi"]
        if any(oi in clean for oi in open_indicators):
            target_app = cls._extract_app_name(clean, is_close=False)
            if target_app:
                return {
                    "intent": "OPEN_APPLICATION",
                    "raw_text": raw_text,
                    "language": "te",
                    "params": {"app_name": target_app}
                }

        # 11. Calculator & Math in Telugu / Tanglish
        # e.g. "క్యాలిక్యులేటర్ ఓపెన్ చేసి 250 ఇంటూ 45 లెక్కించు" / "calculator lo 50 plus 20 entha"
        m_calc = cls._parse_telugu_calculator(clean)
        if m_calc:
            return m_calc

        # If it's a Telugu question or general query -> route to ASK_AI in Telugu
        if is_telugu(raw_text):
            return {
                "intent": "ASK_AI",
                "raw_text": raw_text,
                "language": "te",
                "params": {"query": raw_text}
            }

        return None

    @classmethod
    def _extract_app_name(cls, clean: str, is_close: bool = False) -> str | None:
        """Extracts the target application name from a Telugu or Tanglish phrase."""
        # Check all apps / everything
        if any(w in clean for w in ["అన్నీ", "అన్ని యాప్స్", "యాప్స్ అన్నీ", "all apps", "everything", "all windows"]):
            return "all"

        # Check File Explorer
        if any(w in clean for w in [
            "ఫైల్ ఎక్స్‌ప్లోరర్", "ఫైల్ ఎక్స్ ప్లోరర్", "ఫైల్స్", "ఫైల్",
            "file explorer", "file explore", "files", "folder", "my files", "explorer"
        ]):
            return "file explorer"

        # Check Tab
        if any(w in clean for w in ["ట్యాబ్", "tab", "current tab"]):
            return "tab"

        # Check mapped Telugu names
        for te_name, en_name in APP_NAME_MAP.items():
            if te_name in clean:
                return en_name

        # Strip action verbs and examine leftover words
        verbs = [
            "ఓపెన్ చెయ్యి", "ఓపెన్ చేయ్", "ఓపెన్", "తెరువు", "స్టార్ట్ చెయ్యి",
            "క్లోజ్ చెయ్యి", "క్లోజ్ చేయ్", "క్లోజ్", "మూసివెయ్యి", "మూసివేయి", "ఆపు",
            "open cheyyi", "open chey", "open", "theruvu", "start cheyyi",
            "close cheyyi", "close chey", "close", "moosiveyyi", "moosi"
        ]
        s = clean
        for v in verbs:
            s = s.replace(v, " ")
        # Strip particles
        for p in ["యాప్", "యాప్ ని", "app", "application", "window", "ni", "lo", "ki", "please"]:
            s = re.sub(rf"\b{p}\b", " ", s)

        remainder = s.strip()
        if remainder:
            # Common known English names
            known = [
                "whatsapp", "chrome", "settings", "calculator", "spotify",
                "notepad", "vscode", "visual studio code", "youtube", "word",
                "excel", "powerpoint", "camera", "paint", "edge", "terminal", "cmd"
            ]
            for k in known:
                if k in remainder:
                    return k
            words = remainder.split()
            if words:
                return words[0]

        return "active" if is_close else None

    @classmethod
    def _parse_telugu_whatsapp(cls, raw: str, clean: str) -> dict[str, Any] | None:
        """Parses Telugu and Tanglish WhatsApp messaging instructions."""
        # e.g., "అమ్మకి హాయ్ అని మెసేజ్ పెట్టు"
        # e.g., "whatsapp open chesi Amma ki hi ani message pettu"
        # e.g., "Amma ki message pettu hi ani"
        has_wa = "వాట్సాప్" in clean or "whatsapp" in clean or "వాట్సప్" in clean
        has_msg = any(w in clean for w in ["మెసేజ్", "message", "msg"])
        has_send_verb = any(w in clean for w in ["పెట్టు", "పంపు", "పంపించు", "చేయి", "pettu", "pampu", "send", "cheyyi", "chey"])

        if not ((has_wa or has_msg) and has_send_verb):
            return None

        # Extract recipient contact: look for words preceding 'కి' / 'ki' / 'to'
        contact = None
        m_contact = re.search(r"([a-zA-Z\u0C00-\u0C7F0-9_]+)\s*(?:కి|కు|ki|ku|to)\s+", raw, re.IGNORECASE)
        if m_contact:
            contact = m_contact.group(1).strip()
            # Clean contact if it captured 'whatsapp' or similar
            if contact.lower() in ["whatsapp", "వాట్సాప్", "వాట్సప్"]:
                # Try finding next word
                after = raw[m_contact.end():]
                m_next = re.search(r"([a-zA-Z\u0C00-\u0C7F0-9_]+)\s*(?:కి|కు|ki|ku)\s+", after, re.IGNORECASE)
                if m_next:
                    contact = m_next.group(1).strip()

        # Extract message content: look for text before or after 'అని' / 'ani' / 'saying'
        message = "Hi"
        m_msg_content = re.search(r"['\"]([^'\"]+)['\"]", raw)
        if m_msg_content:
            message = m_msg_content.group(1).strip()
        else:
            # Pattern: "... [message] అని మెసేజ్ ..." or "... message pettu [message] ani"
            m_ani = re.search(r"(?:అని|ani)\s+(?:మెసేజ్|message)", raw, re.IGNORECASE)
            if m_ani:
                # Text before 'ani'
                prefix = raw[:m_ani.start()].strip()
                # Remove contact part from prefix
                if contact and contact in prefix:
                    prefix = prefix.split(contact)[-1].strip()
                # Remove 'కి' / 'ki'
                prefix = re.sub(r"^(?:కి|కు|ki|ku)\s*", "", prefix).strip()
                if prefix:
                    message = prefix
            else:
                m_after_ani = re.search(r"(?:అని|ani)\s*$", raw, re.IGNORECASE)
                m_saying = re.search(r"(?:saying|అని)\s+(.+)", raw, re.IGNORECASE)
                if m_saying:
                    message = m_saying.group(1).strip()

        # Clean message of trailing verbs
        for verb in ["అని మెసేజ్ పెట్టు", "అని మెసేజ్ పంపు", "ani message pettu", "ani message pampu", "message pettu", "message pampu"]:
            message = message.replace(verb, "").strip()

        if not contact:
            contact = "Amma"

        from .task_planner import ActionPlan, TaskStep
        steps = [
            TaskStep(
                step_id=1,
                app_id="whatsapp",
                action="launch_and_focus",
                params={},
                description="Launch and focus WhatsApp",
                critical=True
            ),
            TaskStep(
                step_id=2,
                app_id="whatsapp",
                action="send_message",
                params={"contact": contact, "message": message},
                description=f"Send message to '{contact}' saying '{message}'",
                critical=True
            )
        ]

        plan = ActionPlan(
            plan_id=f"plan_telugu_wa_{contact.lower()}",
            raw_query=raw,
            target_app="whatsapp",
            steps=steps,
            success_response=f"{contact}కి మెసేజ్ విజయవంతంగా పంపబడింది, మాస్టర్."
        )

        return {
            "intent": "EXECUTE_TASK_PLAN",
            "raw_text": raw,
            "language": "te",
            "params": {"plan": plan}
        }


    @classmethod
    def _parse_telugu_calculator(cls, clean: str) -> dict[str, Any] | None:
        """Parses calculator and math expressions in Telugu/Tanglish."""
        has_calc = "క్యాలిక్యులేటర్" in clean or "calculator" in clean or "లెక్కించు" in clean or "lekkimchu" in clean
        has_math_word = any(w in clean for w in ["plus", "minus", "into", "divided by", "ఇంటూ", "ప్లస్", "మైనస్", "భాగాహారం", "entha", "ఎంత"])
        if not (has_calc or has_math_word):
            return None

        # Look for math digits e.g. "250 * 45" or "250 into 45"
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:\+|ప్లస్|plus|\-|మైనస్|minus|\*|x|ఇంటూ|into|గుణించు|\/|divided by|భాగాహారం)\s*(\d+(?:\.\d+)?)", clean)
        if m:
            from .task_planner import task_planner
            plan = task_planner.plan(f"open calculator and calculate {clean}")
            if plan:
                return {
                    "intent": "EXECUTE_TASK_PLAN",
                    "raw_text": clean,
                    "language": "te",
                    "params": {"plan": plan}
                }
        return None

    @classmethod
    def get_response(cls, intent: str, params: dict[str, Any], details: dict[str, Any] | None = None) -> str:
        """
        Generates a natural, respectful human Telugu voice response
        addressing the user as 'మాస్టర్'.
        """
        details = details or {}

        if intent == "GREETING":
            return "నమస్కారం మాస్టర్! డూమ్ ఏఐ మీ సేవలో ఉంది. నేను మీకు ఎలా సహాయపడగలను?"

        elif intent == "OPEN_APPLICATION":
            app = params.get("app_name", "అప్లికేషన్")
            # Map back to natural Telugu name if possible
            app_display = app.capitalize()
            return f"{app_display} ఓపెన్ చేస్తున్నాను, మాస్టర్."

        elif intent == "CLOSE_APPLICATION":
            app = params.get("app_name", "అప్లికేషన్")
            if app == "all":
                return "అన్ని అప్లికేషన్లు క్లోజ్ చేశాను, మాస్టర్."
            elif app == "tab":
                return "ట్యాబ్ క్లోజ్ చేశాను, మాస్టర్."
            elif app == "file explorer":
                return "ఫైల్ ఎక్స్‌ప్లోరర్ క్లోజ్ చేశాను, మాస్టర్."
            return f"{app.capitalize()} క్లోజ్ చేశాను, మాస్టర్."

        elif intent == "LOCK_DEVICE":
            return "ల్యాప్‌టాప్ లాక్ చేస్తున్నాను, మాస్టర్."

        elif intent == "UNLOCK_DEVICE":
            return "స్క్రీన్ అన్‌లాక్ చేయబడింది, మాస్టర్."

        elif intent == "SHUTDOWN_DEVICE":
            return "ల్యాప్‌టాప్ షట్‌డౌన్ చేస్తున్నాను, మాస్టర్."

        elif intent == "RESTART_DEVICE":
            return "ల్యాప్‌టాప్ రీస్టార్ట్ చేస్తున్నాను, మాస్టర్."

        elif intent == "SLEEP_DEVICE":
            return "ల్యాప్‌టాప్ స్లీప్ మోడ్ లోకి వెళ్తోంది, మాస్టర్."

        elif intent == "VOLUME_CONTROL":
            action = params.get("action", "up")
            if action == "up":
                return "వాల్యూమ్ పెంచాను, మాస్టర్."
            elif action == "down":
                return "వాల్యూమ్ తగ్గించాను, మాస్టర్."
            elif action == "mute":
                return "వాల్యూమ్ మ్యూట్ చేశాను, మాస్టర్."
            elif action == "unmute":
                return "వాల్యూమ్ అన్‌మ్యూట్ చేశాను, మాస్టర్."
            return "వాల్యూమ్ సర్దుబాటు చేయబడింది, మాస్టర్."

        elif intent == "WIFI_CONTROL":
            action = params.get("action", "on")
            if action == "on":
                return "వైఫై ఆన్ చేయబడింది, మాస్టర్."
            elif action == "off":
                return "వైఫై ఆఫ్ చేయబడింది, మాస్టర్."
            return "వైఫై కనెక్షన్ సక్రియంగా ఉంది, మాస్టర్."

        elif intent == "BLUETOOTH_CONTROL":
            action = params.get("action", "on")
            if action == "on":
                return "బ్లూటూత్ ఆన్ చేయబడింది, మాస్టర్."
            elif action == "off":
                return "బ్లూటూత్ ఆఫ్ చేయబడింది, మాస్టర్."
            return "బ్లూటూత్ సిద్ధంగా ఉంది, మాస్టర్."

        elif intent == "BRIGHTNESS_CONTROL":
            action = params.get("action", "up")
            level = details.get("brightness_level", params.get("level", 15))
            if action == "up":
                return "బ్రైట్‌నెస్ పెంచాను, మాస్టర్."
            elif action == "down":
                return "బ్రైట్‌నెస్ తగ్గించాను, మాస్టర్."
            elif action == "max":
                return "బ్రైట్‌నెస్ గరిష్టంగా సెట్ చేశాను, మాస్టర్."
            elif action == "min":
                return "బ్రైట్‌నెస్ కనిష్టంగా సెట్ చేశాను, మాస్టర్."
            elif action == "set":
                return f"బ్రైట్‌నెస్ {level} శాతానికి సెట్ చేశాను, మాస్టర్."
            return "బ్రైట్‌నెస్ సర్దుబాటు చేయబడింది, మాస్టర్."

        elif intent == "AIRPLANE_MODE_CONTROL":
            action = params.get("action", "on")
            if action in ["on", "enable"]:
                return "ఏరోప్లేన్ మోడ్ ఆన్ చేయబడింది, మాస్టర్."
            elif action in ["off", "disable"]:
                return "ఏరోప్లేన్ మోడ్ ఆఫ్ చేయబడింది, మాస్టర్."
            return "ఏరోప్లేన్ మోడ్ స్థితి తనిఖీ చేయబడింది, మాస్టర్."

        elif intent == "ACCESSIBILITY_CONTROL":
            feature = params.get("feature", "general")
            action = params.get("action", "open")
            if feature == "magnifier":
                return "మాగ్నిఫైయర్ ఆన్ చేశాను, మాస్టర్." if action in ["on", "open"] else "మాగ్నిఫైయర్ ఆఫ్ చేశాను, మాస్టర్."
            elif feature == "narrator":
                return "నెరేటర్ ఆన్ చేశాను, మాస్టర్." if action in ["on", "open"] else "నెరేటర్ ఆఫ్ చేశాను, మాస్టర్."
            elif feature in ["keyboard", "osk"]:
                return "ఆన్-స్క్రీన్ కీబోర్డ్ ఓపెన్ చేశాను, మాస్టర్." if action in ["on", "open"] else "ఆన్-స్క్రీన్ కీబోర్డ్ క్లోజ్ చేశాను, మాస్టర్."
            elif feature == "highcontrast":
                return "హై కాంట్రాస్ట్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            return "యాక్సెసిబిలిటీ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."

        elif intent == "OPEN_SETTINGS":
            setting = params.get("setting", "general")
            if setting == "display":
                return "డిస్‌ప్లే సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            elif setting == "sound":
                return "సౌండ్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            elif setting == "wifi":
                return "వైఫై సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            elif setting == "bluetooth":
                return "బ్లూటూత్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            elif setting in ["airplane", "aeroplane"]:
                return "ఏరోప్లేన్ మోడ్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            elif setting == "battery":
                return "బ్యాటరీ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."
            return "విండోస్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్."

        elif intent == "SCREENSHOT":
            return "స్క్రీన్‌షాట్ తీసి సేవ్ చేశాను, మాస్టర్."

        elif intent == "GET_DATE_TIME":
            import datetime
            now = datetime.datetime.now()
            q_type = params.get("type", "both")
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%d %B, %Y")
            if q_type == "time":
                return f"ప్రస్తుత సమయం {time_str}, మాస్టర్."
            elif q_type == "date":
                return f"ఈరోజు తేదీ {date_str}, మాస్టర్."
            return f"ప్రస్తుత సమయం {time_str}, తేదీ {date_str}, మాస్టర్."

        elif intent == "SYSTEM_INFO":
            metric = params.get("metric", "battery")
            if metric == "battery":
                import psutil
                bat = psutil.sensors_battery()
                if bat:
                    pct = int(bat.percent)
                    plugged = bool(bat.power_plugged) if bat.power_plugged is not None else False
                    charging_str = "మరియు ఛార్జ్ అవుతోంది" if plugged else "బ్యాటరీ పవర్ లో ఉంది"
                    return f"బ్యాటరీ ప్రస్తుతం {pct} శాతం ఉంది, {charging_str}, మాస్టర్."
                return "బ్యాటరీ సమాచారం అందుబాటులో లేదు, మాస్టర్."
            elif metric == "cpu":
                import psutil
                return f"సిపియు వినియోగం ప్రస్తుతం {int(psutil.cpu_percent(interval=None))} శాతం ఉంది, మాస్టర్."
            elif metric == "ram":
                import psutil
                return f"ర్యామ్ వినియోగం ప్రస్తుతం {int(psutil.virtual_memory().percent)} శాతం ఉంది, మాస్టర్."
            return "సిస్టమ్ పనితీరు అంతా సజావుగా ఉంది, మాస్టర్."

        elif intent == "EXECUTE_TASK_PLAN":
            plan = params.get("plan")
            if plan and getattr(plan, "success_response", None):
                return plan.success_response
            return "టాస్క్ విజయవంతంగా పూర్తయింది, మాస్టర్."

        elif intent == "CONFIRM_ACTION":
            return "ఆదేశం నిర్ధారించబడింది, కొనసాగిస్తున్నాను, మాస్టర్."

        elif intent == "CANCEL_ACTION":
            return "చర్య రద్దు చేయబడింది, మాస్టర్."

        return "సరే మాస్టర్, పని పూర్తయింది."


telugu_engine = TeluguEngine()
