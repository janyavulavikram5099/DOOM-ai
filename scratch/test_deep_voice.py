import subprocess

test_script = """
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Volume = 100
$synth.Rate = -1

# Test SSML for Deep Male Voice
$ssml = @"
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="Microsoft David Desktop">
    <prosody pitch="-5st" rate="-5%" volume="100">
      Doom AI deep voice initialized at maximum volume. At your command, Master.
    </prosody>
  </voice>
</speak>
"@

Write-Host "Speaking SSML deep voice test..."
$synth.SpeakSsml($ssml)
Write-Host "Complete."
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", test_script], capture_output=True, text=True)
print(res.stdout)
print(res.stderr)
