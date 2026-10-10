import re

# 1. Update frontend/js/app.js
app_js_path = r"c:\Users\mones\OneDrive\Desktop\Vikram AI\frontend\js\app.js"
with open(app_js_path, "r", encoding="utf-8") as f:
    app_js = f.read()

app_js = app_js.replace("VIKRAM AI - Main Client Application Coordinator", "DOOM AI - Main Client Application Coordinator")
app_js = app_js.replace("Connected to VIKRAM AI Background Service via WebSocket.", "Connected to DOOM AI Background Service via WebSocket.")
app_js = app_js.replace("this.updateTranscript('VIKRAM',", "this.updateTranscript('DOOM',")
app_js = app_js.replace("vikram_response: result.voice_response", "doom_response: result.voice_response,\n          vikram_response: result.voice_response")
app_js = app_js.replace("// VIKRAM LLM RESPONSE", "// DOOM LLM RESPONSE")
app_js = app_js.replace("const cleanState = (state || '').replace(/^VIKRAM\\s+/i, '').trim();", "const cleanState = (state || '').replace(/^(?:VIKRAM|DOOM)\\s+/i, '').trim();")
app_js = app_js.replace("if (statusLabel) statusLabel.innerText = `VIKRAM ${cleanState}`;", "if (statusLabel) statusLabel.innerText = `DOOM ${cleanState}`;")
app_js = app_js.replace("// Auto-resume when user returns to the VIKRAM tab", "// Auto-resume when user returns to the DOOM tab")
app_js = app_js.replace("Ask Vikram anything", "Ask Doom anything")
app_js = app_js.replace("window.vikramApp = null;", "window.doomApp = null;\nwindow.vikramApp = null;")
app_js = app_js.replace("window.vikramApp = new VikramApp();", "window.doomApp = new VikramApp();\n  window.vikramApp = window.doomApp;")

with open(app_js_path, "w", encoding="utf-8") as f:
    f.write(app_js)

print("frontend/js/app.js updated.")

# 2. Update frontend/js/terminal.js
term_js_path = r"c:\Users\mones\OneDrive\Desktop\Vikram AI\frontend\js\terminal.js"
with open(term_js_path, "r", encoding="utf-8") as f:
    term_js = f.read()

term_js = term_js.replace("VIKRAM AI - Console & Terminal Manager", "DOOM AI - Console & Terminal Manager")
term_js = term_js.replace('<div class="history-vikram">VIKRAM: ${item.vikram_response}</div>', '<div class="history-doom">DOOM: ${item.doom_response || item.vikram_response}</div>')
term_js = term_js.replace("Are you sure you want to reset VIKRAM and unpair this device?", "Are you sure you want to reset DOOM AI and unpair this device?")

with open(term_js_path, "w", encoding="utf-8") as f:
    f.write(term_js)

print("frontend/js/terminal.js updated.")

# 3. Update frontend/js/setup_wizard.js
setup_js_path = r"c:\Users\mones\OneDrive\Desktop\Vikram AI\frontend\js\setup_wizard.js"
with open(setup_js_path, "r", encoding="utf-8") as f:
    setup_js = f.read()

setup_js = setup_js.replace("VIKRAM AI - First-Time Setup Wizard", "DOOM AI - First-Time Setup Wizard")
setup_js = setup_js.replace("Hey Vikram, initialize my voice profile.", "Hey Doom, initialize my voice profile.")

with open(setup_js_path, "w", encoding="utf-8") as f:
    f.write(setup_js)

print("frontend/js/setup_wizard.js updated.")
