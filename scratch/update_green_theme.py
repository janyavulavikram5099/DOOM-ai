import re

hud_path = r"c:\Users\mones\OneDrive\Desktop\Vikram AI\frontend\css\hud.css"

with open(hud_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace root palette and comments
old_palette = """/* ==========================================================================
   VIKRAM AI - Futuristic Desktop HUD Stylesheet
   Color Palette:
   Deep Space Obsidian: #040812 / #070d1d
   Cyber Cyan Glow:    #00f0ff
   Electric Blue:      #0077ff
   Neon Amber Alert:   #ffaa00
   Warning Red:        #ff3366
   Matrix Green:       #00ffaa
   ========================================================================== */

:root {
  --bg-deep: #040812;
  --bg-panel: rgba(8, 16, 32, 0.75);
  --bg-panel-solid: #091224;
  --border-cyan: rgba(0, 240, 255, 0.35);
  --border-glow: 0 0 15px rgba(0, 240, 255, 0.25);
  --cyan-bright: #00f0ff;
  --cyan-dim: #0088aa;
  --blue-electric: #0077ff;
  --neon-amber: #ffaa00;
  --warning-red: #ff3366;
  --success-green: #00ffaa;
  --text-main: #d0e4ff;
  --text-dim: #6884a8;
  --font-brand: 'Orbitron', -apple-system, sans-serif;
  --font-hud: 'Rajdhani', sans-serif;
  --font-mono: 'Fira Code', monospace;
}"""

new_palette = """/* ==========================================================================
   DOOM AI - Futuristic Desktop HUD Stylesheet (Cyber Matrix Emerald Green)
   Color Palette:
   Deep Space Obsidian: #020c07 / #051a10
   Cyber Neon Green:   #00ff88
   Electric Emerald:   #00e676
   Neon Amber Alert:   #ffaa00
   Warning Red:        #ff3366
   Mint Green:         #d5fae7
   ========================================================================== */

:root {
  --bg-deep: #020c07;
  --bg-panel: rgba(4, 22, 14, 0.82);
  --bg-panel-solid: #051a10;
  --border-cyan: rgba(0, 255, 136, 0.35);
  --border-glow: 0 0 15px rgba(0, 255, 136, 0.25);
  --cyan-bright: #00ff88;
  --cyan-dim: #00aa55;
  --blue-electric: #00e676;
  --neon-amber: #ffaa00;
  --warning-red: #ff3366;
  --success-green: #00ff88;
  --text-main: #d5fae7;
  --text-dim: #5c9c78;
  --font-brand: 'Orbitron', -apple-system, sans-serif;
  --font-hud: 'Rajdhani', sans-serif;
  --font-mono: 'Fira Code', monospace;
}"""

content = content.replace(old_palette, new_palette)

# Replace all occurrences of 0, 240, 255 with 0, 255, 136
content = content.replace("0, 240, 255", "0, 255, 136")

# Replace radial gradient background vignette
content = content.replace("rgba(2, 5, 12, 0.85)", "rgba(1, 10, 6, 0.90)")

# Replace history-vikram with history-vikram, .history-doom
content = content.replace(".history-vikram {", ".history-vikram,\n.history-doom {")

# Replace any panel background rgb
content = content.replace("rgba(8, 16, 32, 0.6)", "rgba(4, 22, 14, 0.6)")

with open(hud_path, "w", encoding="utf-8") as f:
    f.write(content)

print("hud.css successfully transformed to Cyber Matrix Green theme!")
