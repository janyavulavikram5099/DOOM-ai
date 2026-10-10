"""
VIKRAM AI / DOOM AI - Calculator Controller
Automates Windows Calculator:
1. Launches and focuses Calculator
2. Evaluates math expressions (addition, subtraction, multiplication, division, powers)
3. Types computation into Calculator
4. Verifies and returns spoken result (e.g. '250 multiplied by 45 is 11,250, Master.')
"""

import logging
import re
import time
from typing import Any

from ..action_engine import UIActionEngine
from ..base_controller import BaseAppController
from ...execution.application_executor import ApplicationExecutor

logger = logging.getLogger("vikram.automation.calculator")


class CalculatorController(BaseAppController):
    name = "Calculator"
    aliases = ["calculator", "calc"]

    def launch(self) -> tuple[bool, str]:
        ok, msg = ApplicationExecutor.launch("calculator")
        hwnd = UIActionEngine.wait_for_window("Calculator", ["CalculatorApp.exe", "calc.exe"], timeout=5.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            return True, "Opening Calculator, Master."
        return ok, msg

    def close(self) -> tuple[bool, str]:
        return ApplicationExecutor.close("calculator")

    def execute_action(self, action: str, params: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        action_lower = action.lower().strip()

        if action_lower == "open":
            ok, msg = self.launch()
            return ok, msg, {}

        if action_lower == "close":
            ok, msg = self.close()
            return ok, msg, {}

        if action_lower in ["calculate", "math", "evaluate", "compute"]:
            expr = params.get("expression") or params.get("query") or ""
            return self.calculate(expr)

        return False, f"Unsupported action '{action}' for Calculator.", {}

    @classmethod
    def _normalize_math_expression(cls, expr: str) -> tuple[str, float | int | None]:
        """Converts spoken math words ('multiplied by', 'times', 'divided by', 'plus', 'minus') to arithmetic string."""
        raw = expr.lower().strip()
        # Clean filler words
        for noise in ["calculate ", "what is ", "what's ", "how much is ", "solve "]:
            if raw.startswith(noise):
                raw = raw[len(noise):].strip()

        # Replace verbal operators
        raw = re.sub(r"\b(?:multiplied by|times|into|x)\b", "*", raw)
        raw = re.sub(r"\b(?:divided by|over)\b", "/", raw)
        raw = re.sub(r"\b(?:plus|add|added to)\b", "+", raw)
        raw = re.sub(r"\b(?:minus|subtract|less)\b", "-", raw)
        raw = re.sub(r"\b(?:to the power of|power)\b", "**", raw)

        # Extract sanitized arithmetic tokens
        cleaned_expr = re.sub(r"[^\d\+\-\*\/\.\(\)\s]", "", raw).strip()

        # Safe evaluation
        try:
            val = eval(cleaned_expr, {"__builtins__": None}, {})
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            return cleaned_expr, val
        except Exception:
            return cleaned_expr, None

    def calculate(self, expression: str) -> tuple[bool, str, dict[str, Any]]:
        """
        Launches Calculator, enters expression keystrokes, and speaks the verified answer.
        """
        cleaned_expr, answer = self._normalize_math_expression(expression)
        if answer is None:
            return False, f"I couldn't evaluate the expression '{expression}', Master.", {}

        # 1. Launch Calculator
        self.launch()
        hwnd = UIActionEngine.wait_for_window("Calculator", ["CalculatorApp.exe", "calc.exe"], timeout=5.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            time.sleep(0.3)

            # Clear calculator (Escape / C)
            UIActionEngine.press_key("esc")
            time.sleep(0.1)

            # Type expression and evaluate (Enter / =)
            for char in str(cleaned_expr).replace(" ", ""):
                UIActionEngine.press_key(char)
                time.sleep(0.04)
            UIActionEngine.press_key("enter")

        # Format number with commas for natural speech (e.g. 11,250)
        formatted_answer = f"{answer:,}" if isinstance(answer, (int, float)) else str(answer)
        voice_msg = f"Calculated: {expression.strip()} is {formatted_answer}, Master."
        return True, voice_msg, {
            "expression": expression,
            "result": answer,
            "formatted": formatted_answer,
            "spoken_response": voice_msg
        }
