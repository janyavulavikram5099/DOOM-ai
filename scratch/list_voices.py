import subprocess

ps = """
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $s.GetInstalledVoices()
foreach ($v in $voices) {
    Write-Host "Name:" $v.VoiceInfo.Name
    Write-Host "Gender:" $v.VoiceInfo.Gender
    Write-Host "Age:" $v.VoiceInfo.Age
    Write-Host "Culture:" $v.VoiceInfo.Culture
    Write-Host "---"
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
print(res.stdout)
