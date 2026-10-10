"""
Integration tests for VIKRAM Developer Mode & Compiler Subsystem.
Tests Java (javac/java), C (gcc), Python, and error diagnostics.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.code_executor import CodeExecutor


class TestDeveloperExecutor(unittest.TestCase):
    def test_java_compilation_and_execution(self):
        # 1. Compile working Java
        ok, msg, det = CodeExecutor.compile_code("samples/Hello.java")
        self.assertTrue(ok, f"Java compilation failed: {det}")
        self.assertIn("Compilation completed successfully", msg)

        # 2. Run compiled Java
        r_ok, r_msg, r_det = CodeExecutor.run_code("samples/Hello.java")
        self.assertTrue(r_ok, f"Java execution failed: {r_det}")
        self.assertIn("operational", r_det.get("stdout", ""))

    def test_java_error_diagnosis(self):
        # Create dedicated test file with deliberate compile error
        err_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "_test_err.java")
        with open(err_file, "w") as f:
            f.write("public class _test_err { public static void main(String[] args) { System.out.println(cannotFindVar); } }")

        try:
            ok, msg, det = CodeExecutor.compile_code("samples/_test_err.java")
            self.assertFalse(ok)
            self.assertIn("Error found", msg)
            self.assertIn("diagnosis", det)
            diag = det["diagnosis"]
            self.assertIn("cannot find symbol", diag.get("error", "").lower())
            self.assertTrue(len(diag.get("suggested_fix", "")) > 0)
        finally:
            if os.path.exists(err_file):
                os.remove(err_file)

    def test_c_compilation_and_execution(self):
        ok, msg, det = CodeExecutor.compile_code("samples/hello.c")
        self.assertTrue(ok, f"C compilation failed: {det}")

        r_ok, r_msg, r_det = CodeExecutor.run_code("samples/hello.c")
        self.assertTrue(r_ok, f"C execution failed: {r_det}")
        self.assertIn("Online", r_det.get("stdout", ""))

    def test_python_execution(self):
        r_ok, r_msg, r_det = CodeExecutor.run_code("samples/hello.py")
        self.assertTrue(r_ok, f"Python execution failed: {r_det}")
        self.assertIn("service, Master", r_det.get("stdout", ""))


if __name__ == "__main__":
    unittest.main()
