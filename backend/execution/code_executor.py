"""
VIKRAM AI - Developer Mode & Code Execution System
Handles compilation, execution, output capture, and error diagnosis for:
Java (javac/java), C/C++ (gcc/g++), Python, and JavaScript (node).
"""

import logging
import os
import shutil
import subprocess
import sys
from typing import Any

from ..ai.provider import LocalAIProvider
from ..assistant.conversation import conversation_context
from .file_executor import FileExecutor

logger = logging.getLogger("vikram.execution.code")


class CodeExecutor:
    @classmethod
    def detect_language(cls, file_path: str) -> str | None:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".java":
            return "java"
        elif ext in [".c"]:
            return "c"
        elif ext in [".cpp", ".cc", ".cxx"]:
            return "cpp"
        elif ext == ".py":
            return "python"
        elif ext in [".js", ".ts"]:
            return "javascript"
        return None

    @classmethod
    def compile_code(cls, file_name: str) -> tuple[bool, str, dict[str, Any]]:
        """
        Compiles source code.
        Returns: (success: bool, voice_response: str, details_dict: dict)
        """
        resolved_path = FileExecutor.resolve_path(file_name)
        if not os.path.exists(resolved_path):
            return False, f"I couldn't find {file_name}.", {"error": "File not found"}

        lang = cls.detect_language(resolved_path)
        if not lang:
            return False, f"Unsupported file type for compilation: {file_name}.", {"error": "Unsupported language"}

        cwd = os.path.dirname(resolved_path)
        base_name = os.path.basename(resolved_path)
        conversation_context.update(current_file=resolved_path, current_language=lang)

        # 1. JAVA COMPILATION
        if lang == "java":
            if not shutil.which("javac"):
                return False, "Java compiler (javac) is not detected in your PATH.", {"error": "Missing JDK"}

            cmd = ["javac", base_name]
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            if result.returncode == 0:
                conversation_context.update(last_compiler_output={"success": True, "output": "Compilation successful"})
                return True, "Compilation completed successfully.", {
                    "file": base_name,
                    "language": "java",
                    "status": "SUCCESS",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                raw_err = result.stderr or result.stdout
                explanation = LocalAIProvider().explain_error(raw_err)
                conversation_context.update(last_compiler_output={"success": False, "output": raw_err}, last_error_analysis=explanation)
                return False, "Error found.", {
                    "file": base_name,
                    "language": "java",
                    "status": "ERROR",
                    "stdout": result.stdout,
                    "stderr": raw_err,
                    "diagnosis": explanation
                }

        # 2. C / C++ COMPILATION
        elif lang in ["c", "cpp"]:
            compiler = "gcc" if lang == "c" else "g++"
            if not shutil.which(compiler):
                return False, f"{compiler.upper()} compiler is not detected in your PATH.", {"error": f"Missing {compiler}"}

            exe_name = os.path.splitext(base_name)[0] + ".exe"
            cmd = [compiler, base_name, "-o", exe_name]
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            if result.returncode == 0:
                conversation_context.update(last_compiler_output={"success": True, "output": "Compilation successful"})
                return True, "Compilation completed successfully.", {
                    "file": base_name,
                    "language": lang,
                    "binary": exe_name,
                    "status": "SUCCESS",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                raw_err = result.stderr or result.stdout
                explanation = LocalAIProvider().explain_error(raw_err)
                conversation_context.update(last_compiler_output={"success": False, "output": raw_err}, last_error_analysis=explanation)
                return False, "Error found.", {
                    "file": base_name,
                    "language": lang,
                    "status": "ERROR",
                    "stdout": result.stdout,
                    "stderr": raw_err,
                    "diagnosis": explanation
                }

        # 3. PYTHON SYNTAX CHECK
        elif lang == "python":
            cmd = [sys.executable, "-m", "py_compile", base_name]
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Python syntax verified successfully.", {
                    "file": base_name,
                    "language": "python",
                    "status": "SUCCESS"
                }
            else:
                raw_err = result.stderr or result.stdout
                explanation = LocalAIProvider().explain_error(raw_err)
                conversation_context.update(last_compiler_output={"success": False, "output": raw_err}, last_error_analysis=explanation)
                return False, "Error found.", {
                    "file": base_name,
                    "language": "python",
                    "status": "ERROR",
                    "stderr": raw_err,
                    "diagnosis": explanation
                }

        return False, f"Cannot compile {file_name}.", {}

    @classmethod
    def run_code(cls, file_name: str) -> tuple[bool, str, dict[str, Any]]:
        """Executes compiled program or script and captures output."""
        resolved_path = FileExecutor.resolve_path(file_name)
        if not os.path.exists(resolved_path):
            return False, f"I couldn't find {file_name}.", {"error": "File not found"}

        lang = cls.detect_language(resolved_path)
        cwd = os.path.dirname(resolved_path)
        base_name = os.path.basename(resolved_path)
        conversation_context.update(current_file=resolved_path, current_language=lang)

        cmd = []
        if lang == "java":
            class_name = os.path.splitext(base_name)[0]
            cmd = ["java", class_name]
        elif lang in ["c", "cpp"]:
            exe_name = os.path.splitext(base_name)[0] + ".exe"
            exe_path = os.path.join(cwd, exe_name)
            if not os.path.exists(exe_path):
                # Attempt to compile first
                c_ok, c_msg, c_det = cls.compile_code(base_name)
                if not c_ok:
                    return False, c_msg, c_det
            cmd = [exe_path]
        elif lang == "python":
            cmd = [sys.executable, base_name]
        elif lang == "javascript":
            cmd = ["node", base_name]
        else:
            return False, f"Unsupported execution for {file_name}.", {}

        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                return True, "Execution completed successfully.", {
                    "file": base_name,
                    "status": "SUCCESS",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode
                }
            else:
                raw_err = result.stderr or result.stdout
                explanation = LocalAIProvider().explain_error(raw_err)
                conversation_context.update(last_compiler_output={"success": False, "output": raw_err}, last_error_analysis=explanation)
                return False, "Error found.", {
                    "file": base_name,
                    "status": "RUNTIME_ERROR",
                    "stdout": result.stdout,
                    "stderr": raw_err,
                    "diagnosis": explanation
                }
        except subprocess.TimeoutExpired:
            return False, "Execution timed out after 20 seconds.", {"error": "TimeoutExpired"}
        except Exception as e:
            return False, f"Execution failed: {e}", {"error": str(e)}

    @classmethod
    def compile_and_run(cls, file_name: str) -> tuple[bool, str, dict[str, Any]]:
        """Sequentially compiles and executes the program."""
        c_ok, c_msg, c_det = cls.compile_code(file_name)
        if not c_ok:
            return False, c_msg, c_det

        r_ok, r_msg, r_det = cls.run_code(file_name)
        if r_ok:
            return True, f"{file_name} compiled and executed successfully.", {
                "compilation": c_det,
                "execution": r_det
            }
        return False, r_msg, {
            "compilation": c_det,
            "execution": r_det
        }

    @classmethod
    def explain_last_error(cls) -> tuple[bool, str, dict[str, Any] | None]:
        """Provides AI explanation of the most recent compiler error."""
        diag = conversation_context.last_error_analysis
        if not diag and conversation_context.last_compiler_output:
            raw = conversation_context.last_compiler_output.get("output", "")
            diag = LocalAIProvider().explain_error(raw)

        if diag:
            expl = diag.get("explanation", "Syntax or symbol resolution error.")
            spoken = f"The error is caused by: {expl}"
            return True, spoken, diag
        return False, "I don't have any recent compiler errors in context to explain.", None
