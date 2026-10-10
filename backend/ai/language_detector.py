"""
VIKRAM AI - Language Detector
Detects the language of incoming speech/text using the langdetect library.
Returns ISO 639-1 codes (en, ta, hi, te, ml, kn, fr, es, ...) for routing
to the correct TTS voice and AI answering pipeline.
"""

import logging

logger = logging.getLogger("vikram.ai.language_detector")

# Supported languages: strictly English and Telugu
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "te": "Telugu",
}

GTTS_LOCALE_MAP: dict[str, str] = {
    "en": "en",
    "te": "te",
}


def detect_language(text: str) -> str:
    """
    Detect language of text. Strictly classifies into two languages:
    1. 'te' (Telugu) - for Telugu Unicode script or transliterated Tanglish.
    2. 'en' (English) - default for all other queries.
    """
    if not text or not text.strip():
        return "en"

    from .telugu_engine import is_telugu
    if is_telugu(text):
        logger.info(f"Language detected: 'te' (Telugu) for text: '{text[:40]}...'")
        return "te"

    try:
        from langdetect import detect, DetectorFactory  # type: ignore[import-untyped]
        DetectorFactory.seed = 0
        code = detect(text)
        if code == "te":
            return "te"
    except Exception:
        pass

    logger.info(f"Language detected: 'en' (English) for text: '{text[:40]}...'")
    return "en"


def get_language_name(lang_code: str) -> str:
    """Returns human-readable language name from ISO code."""
    return LANGUAGE_NAMES.get(lang_code, "English")


def get_gtts_locale(lang_code: str) -> str:
    """Returns the gTTS locale string for a given ISO 639-1 code."""
    return "te" if lang_code == "te" else "en"


def is_english(lang_code: str) -> bool:
    """Returns True if the detected language is English."""
    return lang_code != "te"


def is_telugu_lang(lang_code: str) -> bool:
    """Returns True if the language is Telugu."""
    return lang_code == "te"
