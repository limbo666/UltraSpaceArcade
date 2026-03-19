# 🚀 ULTRA SPACE ARCADE (v0.10)
**A High-Fidelity Evolutionary 2D Arcade Shooter**

Ultra Space Arcade is a tactical, fast-paced space shooter built with Python and Pygame. It features a deep weapon evolution system, complex multi-phase boss battles, and a unique "Nebula Frontier" stage progression system.
<img width="2495" height="1279" alt="screens" src="https://github.com/user-attachments/assets/1ef2759c-1bb4-474b-b843-68701845c340" />

---

## 🕹️ Controls & Navigation
- **Movement**: `WASD` or `Arrow Keys`
- **Primary Fire**: `Spacebar` or `Enter`
- **Nuke (Wipe Screen)**: `Left/Right Ctrl` (Requires pickup)
- **Ghost Shield**: `C` Key (Requires pickup - 3 hits / 20s)
- **ZAPP Beam**: `Z` Key (Manual screen-clearing - 16s recharge)
- **Advance Level (Debug)**: `CTRL + N` (Triple-flash jump)
- **Boss Warp (Debug)**: `L-Shift + D` (Skips to 9.0 Au)

---

## 🔥 Weapon Evolution System (Tiers)
Your arsenal improves dynamically as you collect power-ups:
1. **Tier 1 (Standard)**: Native fire rates for Pellet, Bolt, Shard, Beam, and Flare.
2. **Tier 2 (Evolution)**: Triggered by collecting a duplicate of your current weapon.
   - **Dual/Triple/Blast**: Fire rate is doubled (50% reduction in cooldown).
   - **Laser**: Evolves into the **Super Laser** (40ms fire rate, alternating dual-beams).
3. **Max Tier (Mortar Payload)**: Collecting any weapon power-up while already at Tier 2.
   - **Diagonal Mortars**: Launches two 45-degree projectiles that detonate at 80% screen height.
   - **Effect**: 160px destructive radius; clears projectiles, enemies, and deals heavy Boss damage.

---

## 🛡️ Defensive & Secret Systems
### 1. Ghost Shield
Activated with the `C` key. Deploys a 120-degree cyan energy arc. 
- **Durability**: Absorbs 3 direct hits.
- **Warning**: Rapidly flashes when 1 hit remains or timer is below 5 seconds.

### 2. ZAPP Recharge
A persistent award that clears the horizontal plane of the ship.
- **Cycle**: 16-second recharge. HUD letters transition from **RED** to **GREEN** every 4 seconds.

### 3. Secret Aids
- **Drone Strike**: 15s duration. Twin drones providing synchronized purple laser fire.
- **Ghost Aid**: 150-shot limit. A mirrored projection providing synchronized tactical support from the lower sector.

---

## 👾 Mission Sectors
### Stage 1: The Asteroid Belt
- **Environment**: Grey starfields and rocky planetary bodies.
- **Boss**: **The Twin Cursed Planets**
  - **Mechanics**: 200 HP per hull. No shields.
  - **Rage Mode**: Killing one twin sends the other into a Maroon Rage (Purple eyes, 1.2x speed).
  - **Rage Pulse**: The survivor emits a massive white shockwave every 4 seconds.
  - **Hit Leaking**: Deals damage to "leak" weapon and nuke power-ups.

### Stage 2: The Nebula Frontier
- **Visuals**: Vibrant **Red & Yellow** starfields with **Blue, Green, and Pink** planets.
- **Intensity**: 30% higher enemy density with a 20% surge mid-journey (5.0 Au).
- **Elite Unit**: **Star-Spike Warship**
  - **Design**: Replicated from heavy "EnemyDrone" specs.
  - **Behavior**: Hovers and wanders for 5s firing downward, then launches a locked-trajectory kamikaze charge.

---

## 🔧 Engine Features
- **Chrono-Freeze Impact**: On life loss, the world freezes for 1.8s while particles expand. Includes a RED screen flash and white kinetic pulse ring.
- **Hit-Flashing**: All enemies strobe white when struck for tactile feedback.
- **True Laser Piercing**: Beams pass through multiple targets, dealing continuous damage.
- **Automated Transition**: Seamless cinematic sector jumps with automated cleanup.

---

## 📜 Technical Standards
- **Resolution**: 800x600 Fixed.
- **Typography**: 
  - `Masterpiece.ttf` (Titles)
  - `Orbitron / Epyval.ttf` (HUD/Menu)
  - `13_Misa.TTF` (Awards)
- **License**: Restricted Use (Personal/Experimental only).

---
*Created by [limbo666]. v0.9 Master Distribution.*
