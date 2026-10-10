"""
VIKRAM AI - Gemini AI Q&A Engine
Produces concise, multilingual answers to user questions using:
  1. Gemini 1.5 Flash API (if GEMINI_API_KEY is set) — best quality
  2. Raw DuckDuckGo search snippet (offline-friendly fallback)

The answer is always returned in the same language as the user's question.
"""

import logging
import os

logger = logging.getLogger("vikram.ai.gemini_qa")

# Maximum characters to speak aloud (long answers are truncated for TTS)
MAX_TTS_CHARS = 400
# Maximum search snippet chars to pass to Gemini as context
MAX_CONTEXT_CHARS = 1200


def answer(question: str, search_result: dict, lang_code: str = "en") -> dict:
    """
    Generate an AI answer for the user's question.

    Args:
        question:       The raw user question text
        search_result:  Dict with keys {title, snippet, url, source}
        lang_code:      ISO 639-1 language code ('en', 'ta', 'hi', ...)

    Returns:
        {
          "answer":      Full answer text (for HUD display)
          "tts_answer":  Shortened version for TTS (≤MAX_TTS_CHARS chars)
          "source":      URL of the best source
          "source_title":Title of the source page
          "used_gemini": True if Gemini API was used
          "lang_code":   Echo of detected language
        }
    """
    snippet = search_result.get("snippet", "")
    url = search_result.get("url", "")
    title = search_result.get("title", "")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if api_key:
        result = _gemini_answer(question, snippet, lang_code, api_key)
        if result:
            tts = _shorten_for_tts(result)
            return {
                "answer": result,
                "tts_answer": tts,
                "source": url,
                "source_title": title,
                "used_gemini": True,
                "lang_code": lang_code,
            }

    # Fallback: use raw snippet
    if snippet:
        tts = _shorten_for_tts(snippet)
        return {
            "answer": snippet,
            "tts_answer": tts,
            "source": url,
            "source_title": title,
            "used_gemini": False,
            "lang_code": lang_code,
        }

    # No answer found at all
    not_found = _no_result_message(lang_code)
    return {
        "answer": not_found,
        "tts_answer": not_found,
        "source": "",
        "source_title": "",
        "used_gemini": False,
        "lang_code": lang_code,
    }


def _gemini_answer(question: str, context: str, lang_code: str, api_key: str) -> str | None:
    """Calls Gemini 1.5 Flash to produce a concise answer in the detected language."""
    try:
        import google.generativeai as genai  # type: ignore[import-untyped]
        genai.configure(api_key=api_key)

        lang_instruction = _language_instruction(lang_code)
        context_block = f"\n\nSearch context:\n{context[:MAX_CONTEXT_CHARS]}" if context else ""

        prompt = (
            f"{lang_instruction}\n\n"
            f"User question: {question}"
            f"{context_block}\n\n"
            f"You are DOOM AI, Master's personal desktop assistant.\n"
            f"Provide a heavy, comprehensive, in-depth explanation matching the rich structure of Google Gemini AI:\n"
            f"### Comprehensive Analysis: [Topic Name]\n\n"
            f"#### 1. Executive Overview & Core Definition\n"
            f"(Provide an in-depth conceptual breakdown and thorough explanation)\n\n"
            f"#### 2. Key Dimensions & Fundamental Mechanisms\n"
            f"(Provide bulleted points with **bold headers** explaining inner workings, architecture, or key dimensions)\n\n"
            f"#### 3. Practical Applications & Real-World Impact\n"
            f"(Provide concrete applications, examples, or compilable code if programming related)\n\n"
            f"#### 4. Summary & Strategic Takeaways\n"
            f"(Provide bulleted takeaways and best practices)\n\n"
            f"Use rich markdown formatting with headers and bold key terms. Address Master respectfully."
        )

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text:
            logger.info(f"Gemini answered ({lang_code}): {text[:80]}...")
            return text
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}")
    return None


def _language_instruction(lang_code: str) -> str:
    """Returns a system instruction telling Gemini which language to respond in."""
    lang_map = {
        "ta": "You must answer entirely in Tamil language.",
        "hi": "You must answer entirely in Hindi language.",
        "te": "You must answer entirely in Telugu language.",
        "ml": "You must answer entirely in Malayalam language.",
        "kn": "You must answer entirely in Kannada language.",
        "mr": "You must answer entirely in Marathi language.",
        "bn": "You must answer entirely in Bengali language.",
        "fr": "You must answer entirely in French language.",
        "de": "You must answer entirely in German language.",
        "es": "You must answer entirely in Spanish language.",
        "it": "You must answer entirely in Italian language.",
        "pt": "You must answer entirely in Portuguese language.",
        "ar": "You must answer entirely in Arabic language.",
        "zh-cn": "You must answer entirely in Simplified Chinese.",
        "ja": "You must answer entirely in Japanese language.",
        "ko": "You must answer entirely in Korean language.",
        "ru": "You must answer entirely in Russian language.",
    }
    return lang_map.get(lang_code, "You must answer in English.")


def _shorten_for_tts(text: str) -> str:
    """Truncate text to MAX_TTS_CHARS at a sentence boundary for clean TTS playback."""
    if len(text) <= MAX_TTS_CHARS:
        return text
    truncated = text[:MAX_TTS_CHARS]
    # Try to cut at last sentence-ending punctuation
    for punct in [".", "!", "?", "।", "。"]:
        idx = truncated.rfind(punct)
        if idx > MAX_TTS_CHARS // 2:
            return truncated[: idx + 1]
    return truncated.rstrip() + "..."


def _no_result_message(lang_code: str) -> str:
    """Returns 'no answer found' in the appropriate language."""
    msgs = {
        "ta": "மன்னிக்கவும் Master, அதற்கான பதில் கிடைக்கவில்லை.",
        "hi": "माफ करना Master, इसका जवाब नहीं मिला।",
        "te": "క్షమించండి Master, దానికి సమాధానం దొరకలేదు.",
        "ml": "ക്ഷമിക്കണം Master, അതിനുത്തരം ലഭിച്ചില്ല.",
        "kn": "ಕ್ಷಮಿಸಿ Master, ಅದಕ್ಕೆ ಉತ್ತರ ಸಿಗಲಿಲ್ಲ.",
        "fr": "Désolé Master, je n'ai pas trouvé de réponse.",
        "de": "Entschuldigung Master, keine Antwort gefunden.",
        "es": "Lo siento Master, no encontré respuesta.",
    }
    return msgs.get(lang_code, "Sorry Master, I couldn't find an answer to that.")
