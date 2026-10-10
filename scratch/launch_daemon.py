import subprocess
import sys
import os

py_exe = os.path.abspath(os.path.join(".venv", "Scripts", "python.exe"))
cmd = [py_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8765"]

with open("logs/startup_error.log", "w", encoding="utf-8") as f_err:
    p = subprocess.Popen(
        cmd,
        cwd=os.getcwd(),
        stdout=f_err,
        stderr=subprocess.STDOUT
    )
    print(f"Launched PID: {p.pid}")
