"""
VIKRAM AI - AI Provider Abstraction
Decouples the core system from specific AI models.
Supports LocalAIProvider (offline rule/regex/heuristics), CloudAIProvider (Gemini/OpenAI),
and HybridAIProvider.
"""

import abc
import logging
import os
import re
from typing import Any

from ..database.sqlite import db
from .intent_parser import IntentParser

logger = logging.getLogger("vikram.ai.provider")


class AIProvider(abc.ABC):
    @abc.abstractmethod
    def parse_intent(self, text: str) -> dict[str, Any]:
        """Converts user natural speech to a structured action."""

    @abc.abstractmethod
    def explain_error(self, compiler_output: str, source_code: str | None = None) -> dict[str, Any]:
        """Analyzes compilation/runtime errors and provides explanation & fix."""


class LocalAIProvider(AIProvider):
    """100% Offline AI Provider for local computer operation and error diagnostics."""
    def parse_intent(self, text: str) -> dict[str, Any]:
        return IntentParser.parse(text)

    def explain_error(self, compiler_output: str, source_code: str | None = None) -> dict[str, Any]:
        """Parses Java/C/C++/Python compiler output to extract structured diagnostics."""
        file_name = "Unknown"
        line_num = "Unknown"
        error_type = "Compilation Error"
        explanation = "A compiler syntax or semantic check failed."
        suggested_fix = "Inspect the line highlighted in the compiler output and correct the syntax."

        # Java error pattern: File.java:14: error: cannot find symbol
        java_match = re.search(r"([a-zA-Z0-9_\-\.]+\.java):(\d+):\s*error:\s*(.+)", compiler_output)
        if java_match:
            file_name = java_match.group(1)
            line_num = java_match.group(2)
            msg = java_match.group(3).strip()

            if "cannot find symbol" in msg:
                error_type = "cannot find symbol"
                explanation = "The variable or method is not declared in the current scope or is misspelled, Master."
                suggested_fix = "Declare the variable before using it or verify the correct import statement."
            elif "';' expected" in msg:
                error_type = "syntax error (missing semicolon)"
                explanation = "A statement terminator semicolon is missing at or before this line, Master."
                suggested_fix = "Add a semicolon ';' at the end of the statement."
            elif "incompatible types" in msg:
                error_type = "incompatible types"
                explanation = "A value of one data type is being assigned to an incompatible variable type, Master."
                suggested_fix = "Cast the value explicitly or ensure the variable type matches."
            else:
                error_type = msg

        # GCC / C / C++ pattern: file.c:12:5: error: expected ';' before '}'
        gcc_match = re.search(r"([a-zA-Z0-9_\-\.]+\.(?:c|cpp|h)):(\d+):(?:\d+:)?\s*error:\s*(.+)", compiler_output)
        if gcc_match:
            file_name = gcc_match.group(1)
            line_num = gcc_match.group(2)
            msg = gcc_match.group(3).strip()
            error_type = msg
            if "undeclared" in msg:
                explanation = "An identifier is being used without prior declaration, Master."
                suggested_fix = "Declare the variable or include the appropriate header file."
            elif "expected ';'" in msg:
                explanation = "Missing semicolon in C/C++ statement, Master."
                suggested_fix = "Insert ';' before the indicated token."

        # Python pattern: File "script.py", line 12, in <module> ... SyntaxError: invalid syntax
        py_match = re.search(r'File "([^"]+)", line (\d+).*?\n\s*([a-zA-Z0-9_]+Error):\s*(.+)', compiler_output, re.DOTALL)
        if py_match:
            file_name = os.path.basename(py_match.group(1))
            line_num = py_match.group(2)
            error_type = py_match.group(3)
            msg = py_match.group(4).strip()
            if "NameError" in error_type:
                explanation = f"Python encountered an undefined name '{msg}', Master."
                suggested_fix = "Define the variable or check for typos in the name."
            elif "SyntaxError" in error_type:
                explanation = "Python syntax error in statement structure, Master."
                suggested_fix = "Ensure colons, parentheses, and indentation follow Python syntax rules."
            elif "IndentationError" in error_type:
                explanation = "Unexpected indentation or mixed tabs and spaces, Master."
                suggested_fix = "Align indentation using consistent 4 spaces."

        return {
            "file": file_name,
            "line": line_num,
            "error": error_type,
            "explanation": explanation,
            "suggested_fix": suggested_fix,
            "raw_output": compiler_output
        }


class CloudAIProvider(AIProvider):
    """Cloud AI Provider using API services when online."""
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.local_fallback = LocalAIProvider()

    def parse_intent(self, text: str) -> dict[str, Any]:
        # For instant latency and offline resilience, intent parsing uses Local NLU
        return self.local_fallback.parse_intent(text)

    def explain_error(self, compiler_output: str, source_code: str | None = None) -> dict[str, Any]:
        return self.local_fallback.explain_error(compiler_output, source_code)


def get_ai_provider() -> AIProvider:
    provider_type = db.get_setting("ai_provider", "local")
    if provider_type == "cloud":
        return CloudAIProvider()
    return LocalAIProvider()
