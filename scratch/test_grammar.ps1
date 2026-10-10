Add-Type -AssemblyName System.Speech

$recs = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine($recs[0])
$engine.SetInputToDefaultAudioDevice()

# Wake words
$wakeWords = New-Object System.Speech.Recognition.Choices
$wakeWords.Add([string[]]@("hey doom", "doom", "doom ai", "hey vikram", "vikram"))

# Actions
$actions = New-Object System.Speech.Recognition.Choices
$actions.Add([string[]]@("open", "close", "launch", "exit", "quit", "start"))

# Targets
$targets = New-Object System.Speech.Recognition.Choices
$targets.Add([string[]]@("whatsapp", "chrome", "settings", "file explorer", "notepad", "youtube"))

$gb = New-Object System.Speech.Recognition.GrammarBuilder
$gb.Append($wakeWords, 0, 1)
$gb.Append($actions)
$gb.Append($targets)

$g = New-Object System.Speech.Recognition.Grammar($gb)
$engine.LoadGrammar($g)

Write-Host "Grammar loaded successfully! AudioLevel: $($engine.AudioLevel) AudioState: $($engine.AudioState)"
$engine.Dispose()
