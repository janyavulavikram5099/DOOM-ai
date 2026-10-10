import subprocess
import time

TIMEOUT_SECONDS = 15

ps_code = """
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$engine.SetInputToDefaultAudioDevice()
[Console]::WriteLine("READY")
[Console]::Out.Flush()

for ($i = 0; $i -lt 3; $i++) {
    Start-Sleep -Seconds 1
    [Console]::WriteLine("HEARTBEAT:" + $i)
    [Console]::Out.Flush()
}
"""

p = subprocess.Popen(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    creationflags=subprocess.CREATE_NO_WINDOW,
)

print("Starting read...")
start = time.time()
try:
    # pyrefly: ignore [missing-attribute]
    for line in iter(p.stdout.readline, ""):
        if time.time() - start > TIMEOUT_SECONDS:
            print(f"[TIMEOUT] Exceeded {TIMEOUT_SECONDS}s — killing process.")
            p.kill()
            break
        print(f"[{time.time() - start:.2f}s] Received: {line.strip()}")
finally:
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    print(f"[{time.time() - start:.2f}s] Process exited with code {p.returncode}")

