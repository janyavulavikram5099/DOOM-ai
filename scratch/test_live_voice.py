import time
import sys
sys.path.insert(0, r"c:\Users\mones\OneDrive\Desktop\Vikram AI")

from backend.assistant.text_to_speech import tts

print("Testing deep male voice synthesis with increased volume...")
tts.speak("Hello Master. Doom AI voice has been recalibrated to deep baritone male resonance at maximum output volume.")
time.sleep(5)
print("Speech synthesis complete.")
