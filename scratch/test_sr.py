import subprocess
import time

ps_code = """
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$engine.SetInputToDefaultAudioDevice()
$grammar = New-Object System.Speech.Recognition.DictationGrammar
$engine.LoadGrammar($grammar)

Write-Output "READY_TO_RECOGNIZE"
try {
    $res = $engine.Recognize([TimeSpan]::FromSeconds(3))
    if ($res) {
        Write-Output ("RECOGNIZED:" + $res.Text)
    } else {
        Write-Output "TIMEOUT_NO_SPEECH"
    }
} catch {
    Write-Output ("ERROR:" + $_.Exception.Message)
}
"""

p = subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, err = p.communicate(timeout=10)
print("Out:", out)
print("Err:", err)
