# 🚀 ULTRA SPACE ARCADE — Hotkey Reference

---

## 🚀 Movement _(STATE_PLAYING)_

| Key        | Action                    |
|------------|--------------------------|
| `W` / `↑`  | Move ship up             |
| `S` / `↓`  | Move ship down           |
| `A` / `←`  | Move ship left (+ lean)  |
| `D` / `→`  | Move ship right (+ lean) |

---

## 🔫 Combat _(STATE_PLAYING)_

| Key       | Action                                              |
|-----------|-----------------------------------------------------|
| `SPACE`   | Fire active weapon                                  |
| `X`       | Launch nuke                                         |
| `C`       | Activate shield _(if owned)_                        |
| `Z`       | Fire ZAPP beam _(when unlocked & cooled down)_      |
| `` ` ``   | Instant side drones for 15 seconds                  |

---

## ⏸ System _(Any State)_

| Key   | Action                                              |
|-------|-----------------------------------------------------|
| `ESC` | Pause / Resume / Back in menus                      |
| `F12` | Take screenshot _(saved to game folder)_            |
| `H`   | Toggle HUD display _(panel + keyword letters)_      |

---

## 📋 Menus _(All Menu States)_

| Key               | Action              |
|-------------------|---------------------|
| `↑` / `↓`         | Navigate options    |
| `ENTER` / `SPACE` | Confirm selection   |
| `ESC`             | Back / Resume       |

---

## ✏️ Name Entry _(STATE_NAME_ENTRY)_

| Key               | Action                          |
|-------------------|---------------------------------|
| `↑` / `↓`         | Cycle character                 |
| `ENTER` / `SPACE` | Confirm character & advance     |
| `BACKSPACE`       | Go back one character           |

---

## 🛠 Dev / Debug _(STATE_PLAYING — requires SHIFT)_

| Key            | Action                                             | Notes                                      |
|----------------|----------------------------------------------------|--------------------------------------------|
| `SHIFT + F1`   | Refill lives to 6                                  | —                                          |
| `SHIFT + F2`   | Add 3 nukes                                        | —                                          |
| `SHIFT + F3`   | Jump distance to 9.0 AU                            | Near-boss trigger                          |
| `SHIFT + F4`   | Skip to next stage                                 | Full stage reset                           |
| `SHIFT + F5`   | Trigger boss immediately                           | Sets distance to 9.95                      |
| `SHIFT + F6`   | Max weapon + future pickups at tier 2              | Persists across stages, resets on new game |
| `SHIFT + F7`   | Force weapon → Super Laser (tier 2)                | —                                          |
| `SHIFT + F8`   | Cycle weapon: Dual → Triple → Blast → Laser        | Resets tier to 1                           |

---

## ⚙️ Settings Menu

| Key                          | Action                  |
|------------------------------|-------------------------|
| `↑` / `↓`                    | Navigate options        |
| `ENTER` / `SPACE` / `←` / `→` | Toggle selected option  |
| `ESC`                        | Return to previous menu |

### Available Toggles

| Option       | Effect                                              |
|--------------|-----------------------------------------------------|
| **SFX**      | Enable / disable sound effects                      |
| **MUSIC**    | Enable / disable background music                   |
| **TRAJECTORY** | Enable / disable lean-to-fire direction coupling |

---

## 🗂 Save & Load

| Location                       | Action                                      |
|--------------------------------|---------------------------------------------|
| Pause Menu → **SAVE GAME**      | Save state to `savegame.json`               |
| Main Menu → **LOAD GAME**       | Load saved game _(visible if save exists)_  |

### Saved Data Includes

- Score  
- Lives  
- Nukes  
- Shields  
- Weapon & tier  
- Stage  
- Distance  
- Keyword progress  
- Active states (ZAPP, drones, warp, shield with durations)

---

## 🎵 Music Folder Structure

```plaintext
Music/
├── Stage1/      # Stage 1 gameplay tracks
├── Stage2/      # Stage 2 gameplay tracks
├── Stage3/      # Stage 3 gameplay tracks
├── Boss/        # Boss fight tracks
├── Stage/       # Victory / "Cleared" tracks
└── *.mp3        # Fallback if Stage folders are absent
