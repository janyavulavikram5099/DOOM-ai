import subprocess

ps_code = """
Add-Type -AssemblyName System.Speech
try {
    $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $engine.SetInputToDefaultAudioDevice()
    
    # 1. High-accuracy command grammar
    $choices = New-Object System.Speech.Recognition.Choices
    $choices.Add([string[]]@(
        "hey vikram", "vikram",
        "close whatsapp", "open whatsapp",
        "close chrome", "open chrome",
        "close file explorer", "open file explorer",
        "close notepad", "open notepad",
        "lock laptop", "unlock laptop"
    ))
    $builder = New-Object System.Speech.Recognition.GrammarBuilder
    $builder.Append($choices)
    $cmdGrammar = New-Object System.Speech.Recognition.Grammar($builder)
    $engine.LoadGrammar($cmdGrammar)
    
    # 2. General dictation grammar
    $dictGrammar = New-Object System.Speech.Recognition.DictationGrammar
    $dictGrammar.Weight = 0.5
    $engine.LoadGrammar($dictGrammar)
    
    [Console]::WriteLine("SUCCESS_DUAL_GRAMMAR_LOADED")
} catch {
    [Console]::WriteLine("ERROR:" + $_.Exception.Message)
}
"""

p = subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, err = p.communicate(timeout=6)
print("OUT:", out.strip())
print("ERR:", err.strip())
