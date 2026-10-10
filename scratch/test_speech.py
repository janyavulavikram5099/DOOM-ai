import subprocess

ps_code = """
Add-Type -AssemblyName System.Speech
try {
    $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $engine.SetInputToDefaultAudioDevice()
    [Console]::WriteLine("SUCCESS_SPEECH_INITIALIZED")
} catch {
    [Console]::WriteLine("ERROR:" + $_.Exception.Message)
}
"""

p = subprocess.Popen(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
out, err = p.communicate(timeout=5)
print("OUT:", out.strip())
print("ERR:", err.strip())
