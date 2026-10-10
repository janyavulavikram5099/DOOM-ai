Add-Type -AssemblyName System.Speech
$installed = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
Write-Host "Installed: $($installed.Count)"
foreach ($r in $installed) {
    Write-Host "Recognizer: $($r.Description) Culture: $($r.Culture.Name)"
}
try {
    $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $engine.SetInputToDefaultAudioDevice()
    Write-Host "Audio input set successfully!"
} catch {
    Write-Host "Engine Error: $_"
}
