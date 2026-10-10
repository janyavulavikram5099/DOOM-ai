Add-Type -AssemblyName System.Speech
$recs = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
Write-Host "Count: $($recs.Count)"
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine($recs[0])
$engine.SetInputToDefaultAudioDevice()
Write-Host "Audio device set OK: $($engine.AudioState)"
$engine.Dispose()
Write-Host "Done test."
