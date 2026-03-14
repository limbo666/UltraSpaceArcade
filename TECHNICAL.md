# ULTRA SPACE ARCADE - TECHNICAL DOCUMENTATION

## 🛠️ Architecture Overview
The game is built on a custom state machine utilizing Pygame 2.6.1. It features a robust entity-component-like structure for bullets, enemies, and boss phases.

### Core States
- `STATE_PLAYING`: Active gameplay loop.
- `STATE_PAUSED`: "Chrono-Freeze" state where game logic stops but particles remain active.
- `STATE_DEATH_SEQUENCE`: Scripted impact and explosion sequence.
- `STATE_VICTORY`: Scripted celebratory sequence with fireworks and ship fly-off.

### Key Programming Routines
1. **Weapon Rate Logic**: Fire rate is handled via `actual_rate = base_rate // 2` if `weapon_tier > 1`. Super Laser uses a dedicated toggle bit for alternating offsets.
2. **Impact Sequence**: On collision, the game enters a `paused` state for 1.8s. During this, `draw_frozen_world()` is called while the `particles` update loop remains active, creating a temporal separation effect.
3. **Drone/Ghost Sync**: The `fire()` method iterates through active aids and injects projectiles into the global `bullets` list, utilizing the player's current fire rate for perfect synchronization.
4. **Vector Lasers**: `Bullet.draw()` uses `pygame.transform.rotate` based on the bullet's `angle` or `math.atan2(vy, vx)` to ensure beams point in the direction of travel.
5. **Keyword Recharge**: The ZAPP beam uses a timestamp-based recharge (`zapp_cooldown_timer`). The HUD rendering iterates through the keyword letters, shifting color from RED to GREEN every 4000ms.

## 🔧 Deployment
Run via `python main.py`. Requires `pygame` and high-quality `.wav/.mp3` assets in the `Music` and `Effects` folders (not included in core code distro).
