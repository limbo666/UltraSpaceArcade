import pygame, random, math, os, json, sys
from datetime import datetime

# =============================================================================
# CONSTANTS
# =============================================================================
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600

# Available resolutions — index 0 is the default (800×600)
RESOLUTIONS = [(800, 600), (1024, 768), (1280, 800)]

def _calc_layout(w, h):
    """Return a dict of all derived layout constants for a given (w, h)."""
    return dict(
        SCX              = w  // 2,
        SCY              = h  // 2,
        BOSS_SPAWN_LEFT  = w  // 4,
        BOSS_SPAWN_RIGHT = w  * 3 // 4,
        BOSS_START_Y     = h  // 6,
        BOSS_NORMAL_YMAX = h  * 58 // 100,
        BOSS_RAGE_YTOP   = h  // 5,
        METEOR_MAG_RANGE = w  * 56 // 100,
        HUD_BOTTOM       = h  - 24,
        STAGE_BRIEF_Y    = h  * 72 // 100,
        MENU_TITLE_Y     = h  *  5 // 100,
        MENU_ZONE_TOP    = h  * 23 // 100,
        MENU_ZONE_BOT    = h  * 70 // 100,
        MENU_ITEM_H      = h  *  7 // 100,
        MENU_FRAME_GAP   = h  *  2 // 100,
        MENU_SCORES_Y    = h  * 73 // 100,
        SETT_TITLE_Y     = h  *  8 // 100,
        SETT_ROW_BASE    = h  * 24 // 100,
        SETT_ROW_STEP    = h  * 15 // 100,
        HUD_KW_Y         = h  * 10 // 100,
        HUD_LIVES_Y      = h  *  4 // 100,
    )

def _apply_layout(w, h):
    """Push derived layout values into the module's global namespace."""
    g = globals()
    g.update(_calc_layout(w, h))
    g['SCREEN_WIDTH']  = w
    g['SCREEN_HEIGHT'] = h

# Initialise with default resolution
_apply_layout(SCREEN_WIDTH, SCREEN_HEIGHT)

# Derived layout constants — all positions scale from SCREEN_WIDTH / SCREEN_HEIGHT.
SCX = SCREEN_WIDTH  // 2
SCY = SCREEN_HEIGHT // 2
BOSS_SPAWN_LEFT  = SCREEN_WIDTH  // 4
BOSS_SPAWN_RIGHT = SCREEN_WIDTH  * 3 // 4
BOSS_START_Y     = SCREEN_HEIGHT // 6
BOSS_NORMAL_YMAX = SCREEN_HEIGHT * 58 // 100
BOSS_RAGE_YTOP   = SCREEN_HEIGHT // 5
METEOR_MAG_RANGE = SCREEN_WIDTH  * 56 // 100
HUD_BOTTOM       = SCREEN_HEIGHT - 24
STAGE_BRIEF_Y    = SCREEN_HEIGHT * 72 // 100
MENU_TITLE_Y     = SCREEN_HEIGHT *  5 // 100
MENU_ZONE_TOP    = SCREEN_HEIGHT * 23 // 100
MENU_ZONE_BOT    = SCREEN_HEIGHT * 70 // 100
MENU_ITEM_H      = SCREEN_HEIGHT *  7 // 100
MENU_FRAME_GAP   = SCREEN_HEIGHT *  2 // 100
MENU_SCORES_Y    = SCREEN_HEIGHT * 73 // 100
SETT_TITLE_Y     = SCREEN_HEIGHT *  8 // 100
SETT_ROW_BASE    = SCREEN_HEIGHT * 24 // 100
SETT_ROW_STEP    = SCREEN_HEIGHT * 15 // 100
HUD_KW_Y         = SCREEN_HEIGHT * 10 // 100
HUD_LIVES_Y      = SCREEN_HEIGHT *  4 // 100
SHIP_SPEED    = 6
AU_TIME_MS    = 30000
IDLE_LIMIT_MS = 5000
DRONE_DURATION_MS = 15000
GHOST_MAX_FIRES   = 150
WARP_DURATION_MS  = 15000
BOSS_TRIGGER_AU   = 9.9
BOSS_RADIUS       = 68
HIGHSCORE_FILE    = "highscore.json"
SETTINGS_FILE     = "settings.json"
SAVES_FILE        = "saves.json"
MAX_SAVE_SLOTS    = 10

STATE_INTRO=0; STATE_PLAYING=1; STATE_PAUSED=2; STATE_GAME_OVER=3
STATE_CLEARED=4; STATE_DEATH_SEQUENCE=5; STATE_NAME_ENTRY=6
STATE_CONTINUE=7; STATE_VICTORY=8; STATE_SETTINGS=9
STATE_SAVE_MENU=10; STATE_LOAD_MENU=11; STATE_SAVE_NAME=12

BLACK=(5,5,10); WHITE=(240,240,255); RED=(255,45,80); BLUE=(0,150,255)
CYAN=(0,255,230); YELLOW=(255,230,0); ORANGE=(255,130,0); GREEN=(50,255,100)
PURPLE=(180,50,255); DARK_GRAY=(30,30,40); BROWN=(100,50,20)
GHOST_COLOR=(150,220,255); L_BLUE=(170,220,255); L_GREEN=(170,255,180); L_PINK=(255,180,220)
S3_GOLD=(139,101,8); S3_CORAL=(238,106,80)

ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!?_-()* "

WEAPONS = {
    'normal':      {'color': WHITE,  'speed': 14, 'type': 'pellet', 'rate': 150, 'sound': 'shoot_normal'},
    'dual':        {'color': BLUE,   'speed': 16, 'type': 'bolt',   'rate': 120, 'sound': 'shoot_dual'},
    'triple':      {'color': YELLOW, 'speed': 12, 'type': 'shard',  'rate': 200, 'sound': 'shoot_triple'},
    'laser':       {'color': CYAN,   'speed': 22, 'type': 'beam',   'rate': 100, 'sound': 'shoot_laser'},
    'blast':       {'color': ORANGE, 'speed': 9,  'type': 'flare',  'rate': 280, 'sound': 'shoot_blast'},
    'super_laser': {'color': CYAN,   'speed': 25, 'type': 'beam',   'rate': 40,  'sound': 'shoot_laser'},
}

# =============================================================================
# HELPERS
# =============================================================================
def draw_arcade_symbol(screen, x, y, s_type, color, size=20, glow=True, alpha=255):
    if glow:
        draw_arcade_symbol(screen, x, y, s_type,
                           (color[0]//3, color[1]//3, color[2]//3), size+4, False, alpha)
    surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
    lx, ly = size, size
    if s_type == 'normal':
        pygame.draw.lines(surf, (*color,alpha), False,
                          [(lx-size//2,ly+size//2),(lx,ly-size//2),(lx+size//2,ly+size//2)], 3)
    elif s_type == 'dual':
        pygame.draw.lines(surf, (*color,alpha), False,
                          [(lx-size//2-4,ly+size//2),(lx-4,ly-size//2),(lx+size//2-4,ly+size//2)], 2)
        pygame.draw.lines(surf, (*color,alpha), False,
                          [(lx-size//2+4,ly+size//2),(lx+4,ly-size//2),(lx+size//2+4,ly+size//2)], 2)
    elif s_type == 'triple':
        pygame.draw.lines(surf, (*color,alpha), False,
                          [(lx-size,ly+size//2),(lx-size//2,ly-size//2),(lx,ly+size//2)], 2)
        pygame.draw.lines(surf, (*color,alpha), False,
                          [(lx-size//2,ly+size//2),(lx,ly-size),(lx+size//2,ly+size//2)], 2)
        pygame.draw.lines(surf, (*color,alpha), False,
                          [(lx,ly+size//2),(lx+size//2,ly-size//2),(lx+size,ly+size//2)], 2)
    elif s_type in ('laser','ghost_laser','drone_laser','super_laser'):
        pygame.draw.rect(surf, (*color,alpha), (lx-2, ly-size, 4, size*2))
        pygame.draw.line(surf, (*WHITE,alpha), (lx-size//2,ly-size//2), (lx+size//2,ly-size//2), 2)
    elif s_type in ('blast','ghost_blast'):
        pygame.draw.circle(surf, (*color,alpha), (lx,ly), size//2, 3)
        for i in range(4):
            a = i*(math.pi/2)
            pygame.draw.line(surf, (*WHITE,alpha), (lx,ly),
                             (lx+int(math.cos(a)*size), ly+int(math.sin(a)*size)), 2)
    elif s_type == 'nuke':
        pygame.draw.polygon(surf, (*color,alpha),
                            [(lx,ly-size),(lx-size,ly+size//2),(lx+size,ly+size//2)], 3)
        pygame.draw.circle(surf, (*color,alpha), (lx,ly-2), size//4)
    elif s_type == 'shield':
        pygame.draw.arc(surf, (*CYAN,alpha), (lx-size,ly-size,size*2,size*2), 0, math.pi, 3)
        pygame.draw.circle(surf, (*WHITE,alpha), (lx,ly), size//4)
    elif s_type == 'drone':
        pygame.draw.polygon(surf, (*PURPLE,alpha),
                            [(lx-size//2,ly+size//2),(lx,ly-size//2),(lx+size//2,ly+size//2)], 2)
    elif s_type == 'ghost':
        pygame.draw.polygon(surf, (*CYAN,alpha),
                            [(lx-size//2,ly+size//2),(lx,ly-size//2),(lx+size//2,ly+size//2)], 3)
        pygame.draw.circle(surf, (*WHITE,alpha), (lx,ly), size//4)
    screen.blit(surf, (x-size, y-size))


def draw_pixel_heart(screen, color, x, y, size, reversed_y=False, alpha=255):
    ps  = max(1, size//7)
    pat = [[0,1,1,0,1,1,0],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],
           [0,1,1,1,1,1,0],[0,0,1,1,1,0,0],[0,0,0,1,0,0,0]]
    if reversed_y:
        pat = pat[::-1]
    surf = pygame.Surface((len(pat[0])*ps, len(pat)*ps), pygame.SRCALPHA)
    for r, row in enumerate(pat):
        for c, val in enumerate(row):
            if val:
                pygame.draw.rect(surf, (*color,alpha), (c*ps, r*ps, ps, ps))
                pygame.draw.rect(surf, (0,0,0,alpha),  (c*ps, r*ps, ps, ps), 1)
    screen.blit(surf, (x-surf.get_width()//2, y-surf.get_height()//2))


def _glass_surface(w, h, fill=(6,10,20,215), border=(60,100,200,90)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(fill)
    for row in range(min(40, h)):
        a = int(28*(1.0 - row/min(40, h)))
        pygame.draw.line(s, (80,120,200,a), (2,row), (w-3,row))
    pygame.draw.rect(s, border, (0,0,w,h), 1, border_radius=6)
    pygame.draw.line(s, (130,180,255,60), (4,1), (w-5,1))
    return s


# =============================================================================
# ENTITIES
# =============================================================================
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, speed=1.0):
        self.x, self.y, self.color = x, y, color
        self.vx = (vx if vx is not None else random.uniform(-3,3)) * speed
        self.vy = (vy if vy is not None else random.uniform(-3,3)) * speed
        self.life = 255

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 8

    def draw(self, screen):
        if self.life > 0:
            s = pygame.Surface((3,3), pygame.SRCALPHA)
            s.fill((*self.color, self.life))
            screen.blit(s, (self.x, self.y))


class Bullet:
    def __init__(self, x, y, w_key, angle=0, orbit_angle=0, color=None):
        self.x, self.y = x, y
        self.center_x, self.center_y = x, y
        self.w_key, self.angle, self.orbit_angle = w_key, angle, orbit_angle
        self.config = WEAPONS[w_key] if w_key in WEAPONS else {'color': color or WHITE, 'speed': 18}
        self.color  = self.config['color']
        self.radius = 10 if 'blast' in w_key else 4
        self.rect   = pygame.Rect(x-self.radius, y-self.radius, self.radius*2, self.radius*2)

    def update(self, speed_mult=1.0):
        if 'blast' in self.w_key:
            self.center_y -= self.config['speed'] * speed_mult
            self.orbit_angle += 0.25
            self.x = self.center_x + math.cos(self.orbit_angle)*30
            self.y = self.center_y + math.sin(self.orbit_angle)*30
        else:
            self.x += math.sin(self.angle) * self.config['speed'] * speed_mult
            self.y -= math.cos(self.angle) * self.config['speed'] * speed_mult
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen):
        color = self.config['color']
        if 'laser' in self.w_key or 'super_laser' in self.w_key or 'drone_laser' in self.w_key:
            gs = pygame.Surface((7,32), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*color,48), (0,0,7,32))
            grot = pygame.transform.rotate(gs, -math.degrees(self.angle))
            screen.blit(grot, (self.x-grot.get_width()//2, self.y-grot.get_height()//2))
            surf = pygame.Surface((4,30), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0,0,4,30))
            pygame.draw.rect(surf, WHITE, (1,5,2,20))
            rs = pygame.transform.rotate(surf, -math.degrees(self.angle))
            screen.blit(rs, (self.x-rs.get_width()//2, self.y-rs.get_height()//2))
        elif 'blast' in self.w_key:
            gs = self.radius + 4
            gsurf = pygame.Surface((gs*2,gs*2), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (*color,48), (gs,gs), gs)
            screen.blit(gsurf, (int(self.x)-gs, int(self.y)-gs))
            pygame.draw.circle(screen, color, (int(self.x),int(self.y)), self.radius)
            pygame.draw.circle(screen, WHITE,  (int(self.x),int(self.y)), self.radius-4)
        else:
            gr = self.radius + 3
            gsurf = pygame.Surface((gr*2,gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (*color,52), (gr,gr), gr)
            screen.blit(gsurf, (int(self.x)-gr, int(self.y)-gr))
            pygame.draw.circle(screen, color, (int(self.x),int(self.y)), self.radius)
            pygame.draw.circle(screen, WHITE,  (int(self.x),int(self.y)), max(1,self.radius-1))


class Mortar:
    def __init__(self, x, y, vx, vy, tier=1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.tier      = tier
        self.rect      = pygame.Rect(x-10, y-10, 20, 20)
        self.detonated = False
        self.travel    = 0   # frames in flight, used for visual pulse

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.travel += 1
        self.rect.center = (int(self.x), int(self.y))
        if self.y <= 120:
            self.detonated = True


class Spaceship:
    def __init__(self):
        self.width, self.height = 70, 80
        self.invulnerable_until = 0
        self.lean = 0.0
        self.reset(entering=True)

    def reset(self, entering=False):
        self.target_x = SCREEN_WIDTH//2 - self.width//2
        self.target_y = SCREEN_HEIGHT - self.height - 30
        self.x = self.target_x
        self.y = SCREEN_HEIGHT + 100 if entering else self.target_y
        self.is_entering = entering
        self.rect    = pygame.Rect(self.x, self.y, self.width, self.height)
        self.flicker = 0
        self.lean    = 0.0
        if entering:
            self.invulnerable_until = pygame.time.get_ticks() + 10000

    def is_invulnerable(self, warp=False):
        return self.is_entering or warp or pygame.time.get_ticks() < self.invulnerable_until

    def move(self, keys):
        if self.is_entering:
            if self.y > self.target_y:
                self.y -= 4
            else:
                self.y = self.target_y
            self.lean *= 0.88
        else:
            ml = keys[pygame.K_a] or keys[pygame.K_LEFT]
            mr = keys[pygame.K_d] or keys[pygame.K_RIGHT]
            if ml and self.x > 0:                         self.x -= SHIP_SPEED
            if mr and self.x < SCREEN_WIDTH - self.width: self.x += SHIP_SPEED
            if (keys[pygame.K_w] or keys[pygame.K_UP])   and self.y > SCREEN_HEIGHT//2:            self.y -= SHIP_SPEED
            if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and self.y < SCREEN_HEIGHT - self.height: self.y += SHIP_SPEED
            target_lean = -9.0 if ml else (9.0 if mr else 0.0)
            self.lean  += (target_lean - self.lean) * 0.18
        self.rect.topleft = (self.x, self.y)

    def draw(self, screen, alpha=255, warp=False, strobe=False, shield_active=False, shield_hp=0):
        self.flicker = (self.flicker + 1) % 10
        if strobe and (pygame.time.get_ticks()//40) % 2 == 0:
            return
        elif not strobe and self.is_invulnerable(warp) and self.flicker < 5 and not warp:
            return
        pad = 32
        W   = self.width  + pad*2
        H   = self.height + pad*2 + 40
        surf = pygame.Surface((W, H), pygame.SRCALPHA).convert_alpha()
        lx, ly = pad, pad
        lcx = lx + self.width//2
        lcy = ly + self.height//2
        if warp:
            for i in range(3):
                pygame.draw.circle(surf, random.choice([CYAN,BLUE,WHITE]), (lcx,lcy), 50+i*5, 2)
        if alpha == 255:
            pygame.draw.polygon(surf, ORANGE, [
                (lcx-15, ly+self.height-10),
                (lcx+15, ly+self.height-10),
                (lcx,    ly+self.height+random.randint(10,30))])
        draw_pixel_heart(surf, RED,  lx+12,             ly+self.height-20, 35, True,  alpha)
        draw_pixel_heart(surf, RED,  lx+self.width-12,  ly+self.height-20, 35, True,  alpha)
        draw_pixel_heart(surf, BLUE, lcx, lcy,    75, True,  alpha)
        draw_pixel_heart(surf, CYAN, lcx, lcy-12, 18, False, alpha)
        if shield_active:
            sa = 150 if (pygame.time.get_ticks()//100 % 2 == 0) or shield_hp > 1 else 255
            pygame.draw.arc(surf, (*CYAN,sa),
                            (lx-10, ly-10, self.width+20, self.height+20), 0.2, 2.9, 4)
        if abs(self.lean) > 0.4:
            surf = pygame.transform.rotate(surf, -self.lean)
        bx = self.x + self.width//2  - surf.get_width()//2
        by = self.y + self.height//2 - surf.get_height()//2
        screen.blit(surf, (bx, by))


class Meteorite:
    """Stage-3 enemy: rotating rock with a 1/5-perimeter weak spot.
    Only bullets that strike within the hot arc deal damage.
    Awards 250 points on destruction (10× normal enemy)."""
    SCORE = 250
    ARC_FRAC = 0.2   # 1/5 of the full circle is hittable

    def __init__(self, stage=3):
        self.radius  = random.randint(18, 28)
        self.x       = float(random.randint(self.radius, SCREEN_WIDTH - self.radius))
        self.y       = float(-self.radius * 2)
        self.vy      = random.uniform(1.2, 2.2)   # same speed band as tanks
        self.vx      = 0.0
        self.hp      = 1
        self.color   = (45, 45, 48) if stage <= 3 else (140, 80, 30)  # dark gray s1-3, rust-orange s4
        # Rotation state
        self.angle   = random.uniform(0, math.pi * 2)
        self.spin    = random.choice([-1, 1]) * random.uniform(0.0085, 0.0185)  # half speed
        # Hot arc: spans ARC_FRAC of the circle, offset is fixed relative to body
        self.arc_offset = random.uniform(0, math.pi * 2)
        # Jagged outline offsets (12 verts)
        self.offsets = [self.radius * (0.82 + 0.36 * random.random()) for _ in range(12)]
        self.rect    = pygame.Rect(int(self.x) - self.radius, int(self.y) - self.radius,
                                   self.radius * 2, self.radius * 2)
        self.pulse   = 0.0
        self.hit_flash = 0
        self.shudder   = 0

    def _hot_arc_bounds(self):
        """Return (start_angle, end_angle) of the hittable arc in world space."""
        half = math.pi * self.ARC_FRAC
        mid  = self.angle + self.arc_offset
        return mid - half, mid + half

    def is_hit_valid(self, bx, by):
        """True if bullet centre (bx,by) lands within the hot arc."""
        dx, dy = bx - self.x, by - self.y
        bullet_angle = math.atan2(dy, dx)
        a_start, a_end = self._hot_arc_bounds()
        # Normalise bullet angle into [a_start, a_start+2π) window
        diff = (bullet_angle - a_start) % (math.pi * 2)
        arc_span = (a_end - a_start) % (math.pi * 2)
        return diff <= arc_span

    def hit(self):
        self.hit_flash = 3
        self.shudder   = 4
        self.hp -= 1
        return self.hp <= 0

    def update(self, speed_mult=1.0, particles=None, player_pos=None):
        self.angle  = (self.angle + self.spin * speed_mult) % (math.pi * 2)
        self.pulse  = (self.pulse + 0.07) % (math.pi * 2)
        # Magnetic attraction: nudge toward ship when within 4× max diameter (448px)
        # Only applies while still on-screen — prevents off-screen meteorites drifting back
        on_screen = (-self.radius < self.x < SCREEN_WIDTH + self.radius and
                     -self.radius < self.y < SCREEN_HEIGHT + self.radius)
        if player_pos is not None and on_screen:
            dx, dy = player_pos[0] - self.x, player_pos[1] - self.y
            dist = math.hypot(dx, dy)
            if 0 < dist < METEOR_MAG_RANGE:
                pull = 0.04 * (1.0 - dist / METEOR_MAG_RANGE)   # weak, fades with distance
                self.vx += (dx / dist) * pull
                self.vy += (dy / dist) * pull
                # Cap speed so it never becomes a homing missile
                spd = math.hypot(self.vx, self.vy)
                if spd > 3.5:
                    self.vx = self.vx / spd * 3.5
                    self.vy = self.vy / spd * 3.5
        self.x     += self.vx * speed_mult
        self.y     += self.vy * speed_mult
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.shudder   > 0: self.shudder   -= 1
        self.rect.center = (int(self.x), int(self.y))
        # Faint debris trail
        if particles is not None and random.random() < 0.25:
            particles.append(Particle(self.x + random.uniform(-self.radius*0.4, self.radius*0.4),
                                      self.y + random.uniform(-self.radius*0.4, self.radius*0.4),
                                      (80, 80, 85), speed=0.4))

    def draw(self, screen):
        sx = self.x + (random.randint(-3, 3) if self.shudder > 0 else 0)
        sy = self.y + (random.randint(-3, 3) if self.shudder > 0 else 0)

        # Jagged polygon rotated by self.angle — same style as normal enemies
        pts = [(sx + self.offsets[i] * math.cos(self.angle + i * math.pi / 6),
                sy + self.offsets[i] * math.sin(self.angle + i * math.pi / 6))
               for i in range(12)]

        # Body fill: dark gray (flash white on hit)
        body_col = WHITE if self.hit_flash > 0 else self.color
        pygame.draw.polygon(screen, body_col, pts)

        # Pulsing outer glow (makes it stand out)
        pulse_a = int(50 + 50 * abs(math.sin(self.pulse)))
        gs = pygame.Surface((self.radius*2+14, self.radius*2+14), pygame.SRCALPHA)
        pygame.draw.polygon(gs, (200, 60, 60, pulse_a),
                            [(p[0]-sx+self.radius+7, p[1]-sy+self.radius+7) for p in pts], 4)
        screen.blit(gs, (int(sx)-self.radius-7, int(sy)-self.radius-7))

        # Perimeter segments: white = hot arc (1/5), red = dead zone (4/5)
        # Hot arc spans verts whose angle falls within [a_start, a_end]
        a_start, a_end = self._hot_arc_bounds()
        for i in range(12):
            vert_angle = (self.angle + i * math.pi / 6) % (math.pi * 2)
            # Check if this vertex angle is inside the hot arc window
            diff = (vert_angle - a_start) % (math.pi * 2)
            arc_span = (a_end - a_start) % (math.pi * 2)
            in_arc = diff <= arc_span
            seg_col = WHITE if in_arc else RED
            p1 = pts[i]
            p2 = pts[(i + 1) % 12]
            pygame.draw.line(screen, seg_col, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 2)


class Enemy:
    def __init__(self, is_tank=False, is_unbreakable=False, is_comet=False,
                 is_warship=False, is_angled=False, is_yellow_drone=False, target_pos=None, stage=1):
        self.is_tank        = is_tank
        self.is_unbreakable = is_unbreakable
        self.is_comet       = is_comet
        self.is_warship     = is_warship
        self.is_angled      = is_angled
        self.is_yellow_drone= is_yellow_drone
        self.stage          = stage
        self.hp = 6 if is_tank else (10 if is_comet else (4 if is_warship else 1))
        if is_unbreakable:
            self.hp = 999
        if is_yellow_drone:
            self.hp = 3
        self.max_hp = self.hp
        self.radius = (12 if is_comet else
                       (random.randint(45,60) if (is_tank or is_unbreakable) else
                        (32 if (is_warship or is_yellow_drone) else random.randint(18,28))))
        # Stage 4: angled enemies are 30% larger
        if is_angled and stage == 4:
            self.radius = int(self.radius * 1.3)
        if is_comet:
            self.x, self.y = random.randint(0, SCREEN_WIDTH), -50
            ang = math.atan2(target_pos[1]-self.y, target_pos[0]-self.x)
            self.vx, self.vy = math.cos(ang)*8.0, math.sin(ang)*8.0
            self.color = WHITE
        elif is_yellow_drone:
            self.x, self.y = random.randint(100, SCREEN_WIDTH-100), -50
            self.vx, self.vy = random.choice([-4,4]), 2
            self.color   = (20, 20, 20)
            self.state   = "entry"
            self.timer   = pygame.time.get_ticks() + 10000
            self.last_shot = 0
        elif is_warship:
            self.x, self.y = random.randint(100, SCREEN_WIDTH-100), -50
            self.vx, self.vy = random.choice([-2,2]), 2
            self.color   = (40,0,0)
            self.state   = "entry"
            self.timer   = pygame.time.get_ticks() + 5000
            self.last_shot = 0
        else:
            self.x  = random.randint(self.radius, SCREEN_WIDTH-self.radius)
            self.y  = -self.radius*2
            self.vx = random.choice([-1,1]) * random.uniform(1.5,3.0) if is_angled else 0
            self.vy = (random.uniform(1.0,1.8) if is_unbreakable else
                       (random.uniform(1.2,2.2) if is_tank else random.uniform(3.5,7)))
            if stage == 1:
                self.color = (BROWN if is_unbreakable else
                              ((50,50,70) if is_tank else (110,110,120)))
            elif stage == 2:
                self.color = ((80,0,0) if is_unbreakable else
                              ((0,50,100) if is_tank else (80,50,120)))
            elif stage == 3:
                self.color = (S3_CORAL if is_unbreakable else
                              ((0,50,100) if is_tank else S3_GOLD))
            else:  # stage 4
                self.color = ((0,80,80) if is_unbreakable else
                              ((100,85,15) if is_tank else (55,65,110)))
        self.offsets   = [self.radius*(0.8+0.4*random.random()) for _ in range(12)]
        self.rect      = pygame.Rect(self.x-self.radius, self.y-self.radius,
                                     self.radius*2, self.radius*2)
        self.pulse     = 0
        self.hit_flash = 0
        self.shudder   = 0

    def hit(self):
        if self.is_unbreakable:
            return False
        self.hp       -= 1
        self.hit_flash = 2
        self.shudder   = 4
        if self.is_tank or self.is_comet or self.is_warship:
            self.radius  = max(10, int(self.radius*0.85))
            self.rect    = pygame.Rect(self.x-self.radius, self.y-self.radius,
                                       self.radius*2, self.radius*2)
            self.offsets = [self.radius*(0.8+0.4*random.random()) for _ in range(12)]
        return self.hp <= 0

    def update(self, now, player_pos, bullets, sounds,
               particles=None, speed_mult=1.0, sfx_enabled=True):
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.shudder   > 0: self.shudder   -= 1
        if self.is_warship or self.is_yellow_drone:
            laser_color = YELLOW if self.is_yellow_drone else RED
            if self.state == "entry":
                self.y += self.vy
                if self.y >= 100:
                    self.state = "hover"
            elif self.state == "hover":
                self.x += self.vx
                if self.x < 50 or self.x > SCREEN_WIDTH-50:
                    self.vx *= -1
                if now > self.last_shot + 1000:
                    bullets.append(Bullet(self.x, self.y+20, 'enemy_laser',
                                          angle=math.pi, color=laser_color))
                    self.last_shot = now
                    if sfx_enabled and 'shoot_normal' in sounds:
                        sounds['shoot_normal'].play()
                if now > self.timer:
                    self.state = "kamikaze"
                    ang = math.atan2(player_pos[1]-self.y, player_pos[0]-self.x)
                    self.vx, self.vy = math.cos(ang)*12, math.sin(ang)*12
            elif self.state == "kamikaze":
                self.x += self.vx
                self.y += self.vy
        else:
            self.x += self.vx * speed_mult
            self.y += self.vy * speed_mult
            # Stage 4: tank enemies have weak magnetic pull toward ship
            if self.is_tank and self.stage == 4 and player_pos is not None:
                dx, dy = player_pos[0]-self.x, player_pos[1]-self.y
                dist = math.hypot(dx, dy)
                if 0 < dist < METEOR_MAG_RANGE:
                    pull = 0.03 * (1.0 - dist/METEOR_MAG_RANGE)
                    self.vx += (dx/dist)*pull; self.vy += (dy/dist)*pull
                    spd = math.hypot(self.vx, self.vy)
                    if spd > 2.5: self.vx,self.vy = self.vx/spd*2.5, self.vy/spd*2.5
        self.rect.center = (int(self.x), int(self.y))
        if self.is_unbreakable:
            self.pulse = (self.pulse + 0.1) % (math.pi*2)
        if self.is_comet and particles is not None:
            for _ in range(3):
                particles.append(Particle(self.x, self.y,
                                          random.choice([ORANGE,YELLOW,RED]),
                                          -self.vx*0.5+random.uniform(-1,1),
                                          -self.vy*0.5+random.uniform(-1,1)))

    def draw(self, screen):
        sx = self.x + (random.randint(-4,4) if self.shudder > 0 else 0)
        sy = self.y + (random.randint(-4,4) if self.shudder > 0 else 0)
        if self.is_warship or self.is_yellow_drone:
            acc = YELLOW if self.is_yellow_drone else RED
            out = (60,60,20) if self.is_yellow_drone else (60,60,60)
            pts = [(sx,sy-25),(sx-15,sy-10),(sx-30,sy+10),(sx-10,sy+10),
                   (sx,sy+35),(sx+10,sy+10),(sx+30,sy+10),(sx+15,sy-10)]
            col = WHITE if self.hit_flash > 0 else (30,30,30)
            pygame.draw.polygon(screen, col, pts)
            pygame.draw.polygon(screen, out, pts, 2)
            pygame.draw.polygon(screen, acc, [(sx,sy-10),(sx-15,sy+15),(sx+15,sy+15)])
            pygame.draw.circle(screen, acc, (int(sx-28),int(sy+8)), 4)
            pygame.draw.circle(screen, acc, (int(sx+28),int(sy+8)), 4)
            pygame.draw.circle(screen, acc, (int(sx),   int(sy+32)), 5)
            if self.state == "kamikaze":
                for _ in range(3):
                    pygame.draw.circle(screen, random.choice([acc,WHITE,(255,255,180)] if self.is_yellow_drone else [ORANGE,YELLOW,WHITE]),
                                       (int(sx),int(sy-20)), random.randint(5,12))
            return
        pts = [(sx+self.offsets[i]*math.cos(i*math.pi/6),
                sy+self.offsets[i]*math.sin(i*math.pi/6)) for i in range(12)]
        col = WHITE if self.hit_flash > 0 else self.color
        pygame.draw.polygon(screen, col, pts)
        if self.is_unbreakable:
            pygame.draw.polygon(screen, (int(127+127*math.sin(self.pulse)),0,0), pts, 3)
        elif self.is_comet:
            pygame.draw.polygon(screen, ORANGE, pts, 2)
            pygame.draw.circle(screen, YELLOW, (int(sx),int(sy)), self.radius//2)
        else:
            pygame.draw.polygon(screen, WHITE if self.is_tank else DARK_GRAY, pts, 1)


class BossPlanet:
    def __init__(self, x, side_id, stage=1):
        self.stage = stage
        self.radius = int(BOSS_RADIUS * 0.6)
        self.x, self.y, self.hp, self.max_hp = x, BOSS_START_Y, 200, 200
        self.side_id, self.alpha = side_id, 0
        self.vx = random.uniform(2.1,4.2) * (1 if side_id==0 else -1)
        self.vy, self.last_move_change = random.uniform(-1.4,1.4), 0
        self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius,
                                self.radius*2, self.radius*2)
        self.is_rage        = False
        self.shake_timer    = 0
        self.is_dying       = False
        self.death_timer    = 0
        self.rage_attack_timer = 0
        self._rage_radius_target = int(BOSS_RADIUS * 0.3)
        self._rage_descent_vy    = -0.6
        # Per-stage palette: (body_dark, body_mid, spike_col, eye_fill, eye_glow)
        self._pal = {
            1: ((55,15,5),   (90,28,8),    (190,25,10),  (220,35,10),  (255,130,0)),   # volcanic
            2: ((12,38,8),   (25,65,12),   (20,170,35),  (30,210,45),  (160,255,60)),  # toxic
            3: ((18,8,28),   (32,10,42),   (155,0,185),  (195,0,225),  (255,80,255)),  # void/cursed
        }
        self._regen_shape()

    def _regen_shape(self):
        """Chunky irregular body blob + separate spike shard definitions, seeded for consistency."""
        r = self.radius
        random.seed(self.side_id * 1000 + self.stage * 100 + int(r))
        # Body: 16-point angular blob — NOT circular, more like a rough rock
        self._body_pts = []
        n_body = 16
        for i in range(n_body):
            ang = i * math.pi * 2 / n_body
            dist = r * (random.uniform(0.72, 0.92) if i % 2 == 0 else random.uniform(0.52, 0.74))
            self._body_pts.append((dist, ang))
        # Spikes: sharp triangular shards — more per stage
        n_spikes = 10 + self.stage * 3   # 13 / 16 / 19
        self._spikes = []
        for _ in range(n_spikes):
            ang    = random.uniform(0, math.pi*2)
            length = r * random.uniform(0.50, 0.95)
            width  = r * random.uniform(0.09, 0.20)
            base_r = r * random.uniform(0.68, 0.88)
            self._spikes.append((ang, length, width, base_r))
        random.seed()

    def _body_polygon(self, cx, cy):
        return [(cx + d*math.cos(a), cy + d*math.sin(a)) for d,a in self._body_pts]

    def _spike_triangles(self, cx, cy):
        tris = []
        for ang, length, width, base_r in self._spikes:
            bx = cx + base_r * math.cos(ang);  by = cy + base_r * math.sin(ang)
            tx = cx + (base_r+length) * math.cos(ang); ty = cy + (base_r+length) * math.sin(ang)
            perp = ang + math.pi/2
            lx = bx + width*math.cos(perp); ly = by + width*math.sin(perp)
            rx = bx - width*math.cos(perp); ry = by - width*math.sin(perp)
            tris.append(((int(tx),int(ty)), (int(lx),int(ly)), (int(rx),int(ry))))
        return tris

    def update(self):
        now = pygame.time.get_ticks()
        if self.is_dying: return None
        if self.alpha < 255: self.alpha += 2

        if self.is_rage:
            if self.radius > self._rage_radius_target:
                self.radius = max(self._rage_radius_target, self.radius - 0.25)
                self._regen_shape()
            mf = 2000
            if now - self.last_move_change > mf:
                self.vx = random.uniform(6.2, 9.7) * (1 if self.vx > 0 else -1)
                self.vy = self._rage_descent_vy
                self.last_move_change = now
            self.x += self.vx; self.y += self.vy
            if self.x < self.radius or self.x > SCREEN_WIDTH - self.radius: self.vx *= -1
            if self.y < self.radius:
                self.y = float(self.radius); self.vy = abs(self.vy)
            elif self.y > BOSS_RAGE_YTOP:
                self.y = float(BOSS_RAGE_YTOP); self.vy = -abs(self.vy)
        else:
            mf = 4000
            if now - self.last_move_change > mf:
                self.vx = random.uniform(2.1,4.2) * (1 if self.vx > 0 else -1)
                self.vy = random.uniform(-1.4,1.4)
                self.last_move_change = now
            self.x += self.vx; self.y += self.vy
            if self.x < self.radius or self.x > SCREEN_WIDTH-self.radius: self.vx *= -1
            if self.y < 50          or self.y > BOSS_NORMAL_YMAX:         self.vy *= -1

        self.rect.center = (int(self.x), int(self.y))
        if self.shake_timer > 0: self.shake_timer -= 1
        if self.is_rage and now > self.rage_attack_timer:
            self.rage_attack_timer = now + 3000
            return "shockwave"
        return None

    def draw(self, screen):
        now = pygame.time.get_ticks()
        if self.is_dying:
            if (now//50) % 2 == 0: return
            alpha = max(0, 255-(now-self.death_timer)//4)
        else:
            alpha = max(0, min(255, int(self.alpha)))

        self.rect = pygame.Rect(int(self.x)-self.radius, int(self.y)-self.radius,
                                self.radius*2, self.radius*2)
        sx = self.x + random.randint(-2,2) if self.shake_timer > 0 else self.x
        sy = self.y + random.randint(-2,2) if self.shake_timer > 0 else self.y

        pal = self._pal.get(self.stage, self._pal[1])
        body_dark, body_mid, spike_col, eye_fill, eye_glow = pal

        pulse = abs(math.sin(now * 0.006))
        if self.is_rage:
            pr = int(80 + 70*pulse)
            body_dark = (pr, 0, 0);  body_mid = (min(255,pr+40), 0, 0)
            spike_col = (min(255,pr+80), 0, 0)
            eye_glow  = (220, 0, 220); eye_fill = (200, 0, 0)

        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 1 — Spike shards behind body
        for tri in self._spike_triangles(sx, sy):
            pygame.draw.polygon(s, (*spike_col, min(alpha, 215)), tri)
            pygame.draw.polygon(s, (5, 2, 8, min(alpha, 160)), tri, 1)

        # 2 — Chunky body blob
        body = self._body_polygon(sx, sy)
        pygame.draw.polygon(s, (*body_dark, alpha), body)
        # Subtle mid-tone inner face (offset toward top-left for cartoon shading)
        inner = [(x + (sx-x)*0.14 - 1, y + (sy-y)*0.14 - 1) for x,y in body]
        pygame.draw.polygon(s, (*body_mid, min(alpha, 140)), inner)
        # Hard dark outline — key to the cartoon look
        pygame.draw.polygon(s, (4, 2, 8, alpha), body, 3)

        # 3 — Downward-pointing triangle eyes (fixed to face, not rotating)
        r = self.radius
        ew = r * 0.26        # half-width of each eye triangle
        eh = r * 0.32        # height (tip points DOWN)
        ey_top = sy - r * 0.10
        gap    = r * 0.10    # gap between the two eyes

        for sign in (-1, 1):
            cx_e = sx + sign * (ew + gap * 0.5)
            tl  = (int(cx_e - ew), int(ey_top))
            tr  = (int(cx_e + ew), int(ey_top))
            tip = (int(cx_e),      int(ey_top + eh))
            # Glow halo (slightly larger triangle, drawn first)
            gl = 3
            glow_tri = [(tl[0]-gl, tl[1]-gl), (tr[0]+gl, tr[1]-gl), (tip[0], tip[1]+gl+1)]
            pygame.draw.polygon(s, (*eye_glow, min(alpha, 255)), glow_tri, 3)
            # Filled eye
            pygame.draw.polygon(s, (*eye_fill, alpha), [tl, tr, tip])
            # Bright top edge highlight
            pygame.draw.line(s, (*eye_glow, min(alpha, 220)), tl, tr, 2)

        # 4 — Rage pulsing outline
        if self.is_rage and not self.is_dying:
            ra = int(180 + 75*pulse)
            pygame.draw.polygon(s, (ra, 0, 0, int(180*pulse)), body, 4)

        screen.blit(s, (0,0))

        # 5 — Health bar
        if not self.is_dying:
            hbw = 100
            pygame.draw.rect(screen, DARK_GRAY,
                             (int(self.x-hbw//2), int(self.y-self.radius-20), hbw, 8))
            pygame.draw.rect(screen, RED if not self.is_rage else YELLOW,
                             (int(self.x-hbw//2), int(self.y-self.radius-20),
                              int(hbw*(self.hp/self.max_hp)), 8))
            if self.is_rage:
                pulse_c = abs(math.sin(now * 0.005))
                ca = int(160 + 95*pulse_c)
                cy0 = int(self.y - self.radius - 36); cx0 = int(self.x)
                for row in range(3):
                    oy = cy0 + row*7
                    chev = [(cx0-10+row*3, oy+7), (cx0, oy), (cx0+10-row*3, oy+7)]
                    cs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.lines(cs, (255, 40, 40, ca - row*40), False, chev, 2)
                    screen.blit(cs, (0,0))


class BossProjectile:
    def __init__(self, x, y, vx, vy, size=20, color=WHITE):
        self.x,self.y,self.vx,self.vy,self.size,self.color = x,y,vx,vy,size,color
        self.rect = pygame.Rect(x-size//2, y-size//2, size, size)

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen):
        pygame.draw.polygon(screen, self.color,
                            [(self.x,self.y+self.size),
                             (self.x-self.size//2,self.y-self.size//2),
                             (self.x+self.size//2,self.y-self.size//2)])


class LetterItem:
    def __init__(self, x, y, char):
        self.x, self.y, self.char = x, y, char
        self.rect  = pygame.Rect(x-15, y-15, 30, 30)
        self.pulse = 0

    def update(self):
        self.y += 2
        self.pulse = (self.pulse + 0.1) % (math.pi*2)
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, font):
        val   = int(150+100*math.sin(self.pulse))
        color = (val, val, 255)
        img   = font.render(self.char, True, color)
        gs    = max(img.get_width(), img.get_height()) + 15
        s     = pygame.Surface((gs,gs), pygame.SRCALPHA)
        pygame.draw.circle(s, (0,100,255,60), (gs//2,gs//2), gs//2)
        screen.blit(s,   (self.x-gs//2, self.y-gs//2))
        screen.blit(img, (self.x-img.get_width()//2, self.y-img.get_height()//2))


class PowerUp:
    def __init__(self, x, y, p_type):
        self.x, self.y, self.p_type = x, y, p_type
        self.rect       = pygame.Rect(x-20, y-20, 40, 40)
        self.start_x    = x
        self.angle      = 0
        self.pulse_size = 18.0
        self.color = (PURPLE if p_type in ('drone','ghost') else
                      (CYAN  if p_type == 'shield' else
                       (GREEN if p_type == 'nuke'  else WEAPONS[p_type]['color'])))

    def update(self):
        self.angle += 0.04
        self.x = self.start_x + math.sin(self.angle)*60
        self.y += 2.5
        self.rect.center = (int(self.x), int(self.y))
        self.pulse_size  = 18.0 + 3.0*math.sin(self.angle*4)

    def draw(self, screen):
        draw_arcade_symbol(screen, int(self.x), int(self.y),
                           self.p_type, self.color, int(self.pulse_size))


class Planet:
    def __init__(self, stage=1): self.reset(stage)

    def reset(self, stage=1):
        self.x, self.y = random.randint(0,SCREEN_WIDTH), random.randint(-1000,-100)
        self.radius     = random.randint(40,120)
        self.speed      = random.uniform(0.3,0.8)
        if stage == 1:
            base = random.randint(20,50); self.color = (base,base,base+20)
        elif stage == 2:
            self.color = random.choice([L_BLUE,L_GREEN,L_PINK])
        elif stage == 3:
            self.color = random.choice([(78,82,92),(44,108,62),(52,72,138)])
        else:  # stage 4 — dark mustard, dark green, light gray
            self.color = random.choice([(110,90,20),(30,70,30),(180,185,190)])
        self.craters = [(random.randint(-self.radius//2,self.radius//2),
                         random.randint(-self.radius//2,self.radius//2),
                         random.randint(5,15)) for _ in range(5)]
        self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius,
                                self.radius*2, self.radius*2)
        self.has_atm   = random.random() < 0.55
        self.atm_phase = random.uniform(0, math.pi*2)
        ar = int(self.radius*1.45)
        if self.has_atm:
            self._atm = pygame.Surface((ar*2,ar*2)).convert()
            self._atm.fill((0,0,0)); self._atm.set_colorkey((0,0,0))
            pygame.draw.circle(self._atm,
                               (min(255,self.color[0]+40),
                                min(255,self.color[1]+40),
                                min(255,self.color[2]+60)), (ar,ar), ar)
        self._ar = ar

    def update(self, speed_mult=1.0, stage=1):
        self.y += self.speed * speed_mult
        self.atm_phase += 0.025
        self.rect.center = (int(self.x), int(self.y))
        if self.y > SCREEN_HEIGHT + self.radius: self.reset(stage)

    def draw(self, screen, offset=(0,0)):
        if self.has_atm:
            self._atm.set_alpha(int(16+14*math.sin(self.atm_phase)))
            screen.blit(self._atm, (int(self.x-self._ar+offset[0]),
                                    int(self.y-self._ar+offset[1])))
        pygame.draw.circle(screen, self.color,
                           (int(self.x+offset[0]),int(self.y+offset[1])), self.radius)
        for cx, cy, cr in self.craters:
            pygame.draw.circle(screen,
                               (max(0,self.color[0]-20),
                                max(0,self.color[1]-20),
                                max(0,self.color[2]-20)),
                               (int(self.x+cx+offset[0]),
                                int(self.y+cy+offset[1])), cr)


# =============================================================================
# GAME
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ULTRA SPACE ARCADE v0.18")
        self.clock     = pygame.time.Clock()
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.highscore_path = os.path.join(self.base_path, HIGHSCORE_FILE)
        res = os.path.join(self.base_path, "Resourses")

        def _font(n, s):
            p = os.path.join(res, n)
            return (pygame.font.Font(p, s) if os.path.exists(p)
                    else pygame.font.SysFont("monospace", s, bold=True))

        self.title_font     = _font("Masterpiece.ttf", 60)
        self.misa_font      = _font("13_Misa.TTF", 22)
        self.menu_font      = _font("Orbitron-VariableFont_wght.ttf", 20)
        self.countdown_font = _font("Orbitron-VariableFont_wght.ttf", 48)
        self.info_font      = _font("Epyval.ttf", 16)

        self.init_stars(1)
        self._init_nebulas(1)
        self._init_pulsars(1)
        self.planets   = [Planet(1) for _ in range(3)]
        self.particles = []
        self.shake     = 0
        self.last_fire = 0
        self.screenshot_flash   = 0
        self.pending_screenshot = False
        self.display_score = 0
        self.hud_jitter    = 0
        self.save_flash    = 0

        self.load_audio()          # populates self.title_tracks etc.
        self.load_highscores()
        self.load_settings()
        self._apply_resolution()   # resize display to saved resolution
        self._create_vignette()
        self._create_hud_panel()

        self.state      = STATE_INTRO
        self.menu_idx   = 0
        self.menu_count = 3

        # save/load UI state
        self.save_slots_list  = []
        self.sm_idx           = 0
        self.lm_idx           = 0
        self.sm_name_input    = ""
        self.sm_overwrite_idx = None
        self.sm_confirm       = False
        self.sm_origin        = STATE_PAUSED
        self.load_saves()
        self.reset_game(True)

        # Start title music AFTER reset_game (which calls play_next_track for STATE_PLAYING)
        self.play_title_music()

    # ── Background layers ─────────────────────────────────────────────────────
    def init_stars(self, stage):
        def mk(n, sz, spd, cols):
            return [[random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT),
                     random.uniform(*spd), random.choice(cols), sz] for _ in range(n)]
        if stage == 1:
            bc=[(55,55,65),(45,45,58)]; mc=[(170,170,190),(200,200,215)]; fc=[(90,185,255),(70,140,240),(140,210,255)]
        elif stage == 2:
            bc=[(65,25,25),(55,35,35)]; mc=[(210,170,160),(245,185,130)]; fc=[(255,90,70),(255,185,40),(245,130,80)]
        elif stage == 3:
            bc=[(50,50,20),(35,35,14)]; mc=[(200,200,130),(220,220,150)]; fc=[(255,245,80),(140,160,255),(235,235,210)]
        else:  # stage 4 — void rift: yellow-white and blue stars
            bc=[(20,20,35),(15,15,28)]; mc=[(200,200,160),(230,230,180)]; fc=[(255,250,180),(240,245,255),(80,140,255)]
        self.stars_bg  = mk(65,1,(0.18,0.45),bc)
        self.stars_mid = mk(45,1,(0.50,1.20),mc)
        self.stars_fg  = mk(22,2,(1.00,2.50),fc)

    def _init_nebulas(self, stage):
        palette = ([(45,0,75),(0,20,60),(10,10,50)]  if stage==1 else
                   [(65,0,0),(48,0,48),(0,28,58)]     if stage==2 else
                   [(28,24,0),(22,26,4),(10,18,28)]   if stage==3 else
                   [(35,28,0),(28,22,0),(18,14,5)])
        self.nebulas = []
        for i in range(3):
            rx,ry = random.randint(110,195),random.randint(70,135)
            col   = palette[i%len(palette)]; alph = random.randint(22,38)
            surf  = pygame.Surface((rx*2,ry*2),pygame.SRCALPHA).convert_alpha()
            pygame.draw.ellipse(surf,(*col,alph),(0,0,rx*2,ry*2))
            self.nebulas.append({'x':float(random.randint(80,SCREEN_WIDTH-80)),
                                  'y':float(random.randint(-100,SCREEN_HEIGHT)),
                                  'rx':rx,'ry':ry,'speed':random.uniform(0.035,0.09),'surf':surf})

    def _draw_nebulas(self, off):
        for nb in self.nebulas:
            nb['y'] += nb['speed']
            if nb['y']-nb['ry'] > SCREEN_HEIGHT:
                nb['y'] = float(-nb['ry'])
                nb['x'] = float(random.randint(80,SCREEN_WIDTH-80))
            self.screen.blit(nb['surf'],(int(nb['x']-nb['rx']+off[0]),
                                         int(nb['y']-nb['ry']+off[1])))

    def _init_pulsars(self, stage):
        if stage < 3: self.pulsars=[]; return
        self.pulsars = [{'x':float(random.randint(0,SCREEN_WIDTH)),
                          'y':float(random.randint(-SCREEN_HEIGHT,SCREEN_HEIGHT)),
                          'speed':random.uniform(0.04,0.12),
                          'phase':random.uniform(0,math.pi*2),
                          'phase_spd':random.uniform(0.006,0.018),
                          'size':random.choice([1,1,1,2])} for _ in range(24)]

    def _draw_pulsars(self, off):
        for p in self.pulsars:
            p['y']+=p['speed']; p['phase']+=p['phase_spd']
            if p['y']>SCREEN_HEIGHT+4:
                p['y']=float(random.randint(-350,-4)); p['x']=float(random.randint(0,SCREEN_WIDTH))
            alpha=int((math.sin(p['phase'])*0.5+0.5)*255)
            if alpha<10: continue
            t=alpha/255.0; col=(int(240+15*t),int(218+22*t),int(55+200*t)); sz=p['size']
            gs=pygame.Surface((sz*2+2,sz*2+2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*col,alpha),(sz+1,sz+1),sz)
            self.screen.blit(gs,(int(p['x']-sz+off[0]),int(p['y']-sz+off[1])))

    def _create_vignette(self):
        v  = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA).convert_alpha()
        cx,cy = SCREEN_WIDTH//2,SCREEN_HEIGHT//2; mr=int(math.hypot(cx,cy))+20
        for i in range(50):
            r=mr-i*(mr//50); a=max(0,int(115*(1.0-i/50)))
            pygame.draw.circle(v,(0,0,0,a),(cx,cy),r)
        self.vignette=v

    def _create_hud_panel(self):
        self.hud_panel = _glass_surface(192,163)

    # ── Settings ──────────────────────────────────────────────────────────────
    def load_settings(self):
        self.sfx_enabled=True; self.music_enabled=True; self.trajectory_enabled=True
        self.sfx_volume=0.55; self.music_volume=0.4
        self.sfx_volume_saved=0.55; self.music_volume_saved=0.4
        self.resolution_idx=0
        path=os.path.join(self.base_path,SETTINGS_FILE)
        if os.path.exists(path):
            try:
                with open(path,'r') as f: s=json.load(f)
                self.sfx_enabled        = bool(s.get('sfx_enabled',True))
                self.music_enabled      = bool(s.get('music_enabled',True))
                self.trajectory_enabled = bool(s.get('trajectory_enabled',True))
                self.sfx_volume         = float(s.get('sfx_volume',0.55))
                self.music_volume       = float(s.get('music_volume',0.4))
                self.sfx_volume_saved   = float(s.get('sfx_volume_saved',0.55))
                self.music_volume_saved = float(s.get('music_volume_saved',0.4))
                self.resolution_idx     = int(s.get('resolution_idx',0)) % len(RESOLUTIONS)
            except Exception: pass
        self._apply_volumes()

    def _apply_volumes(self):
        """Sync pygame mixer volumes from current settings state."""
        for snd in self.sounds.values(): snd.set_volume(self.sfx_volume)
        pygame.mixer.music.set_volume(self.music_volume)

    def _apply_resolution(self):
        """Resize the display and rebuild all resolution-dependent resources."""
        w, h = RESOLUTIONS[self.resolution_idx]
        _apply_layout(w, h)
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
        self.screen = pygame.display.set_mode((w, h))
        # Rebuild fonts at new scale (base sizes designed for 600px height)
        scale = h / 600.0
        res = os.path.join(self.base_path, "Resourses")
        def _font(n, s):
            p = os.path.join(res, n)
            return (pygame.font.Font(p, max(8, int(s * scale)))
                    if os.path.exists(p) else pygame.font.SysFont("monospace", max(8, int(s * scale)), bold=True))
        self.title_font     = _font("Masterpiece.ttf", 60)
        self.misa_font      = _font("13_Misa.TTF", 22)
        self.menu_font      = _font("Orbitron-VariableFont_wght.ttf", 20)
        self.countdown_font = _font("Orbitron-VariableFont_wght.ttf", 48)
        self.info_font      = _font("Epyval.ttf", 16)
        self._create_vignette()
        self._create_hud_panel()
        self.init_stars(self.stage if hasattr(self,'stage') else 1)
        self._init_nebulas(self.stage if hasattr(self,'stage') else 1)
        self._init_pulsars(self.stage if hasattr(self,'stage') else 1)
        self.save_settings()

    def save_settings(self):
        try:
            with open(os.path.join(self.base_path,SETTINGS_FILE),'w') as f:
                json.dump({'sfx_enabled':self.sfx_enabled,
                           'music_enabled':self.music_enabled,
                           'trajectory_enabled':self.trajectory_enabled,
                           'sfx_volume':round(self.sfx_volume,2),
                           'music_volume':round(self.music_volume,2),
                           'sfx_volume_saved':round(self.sfx_volume_saved,2),
                           'music_volume_saved':round(self.music_volume_saved,2),
                           'resolution_idx':self.resolution_idx},f,indent=2)
        except Exception: pass

    # ── Multi-slot Save / Load ────────────────────────────────────────────────
    def _saves_path(self): return os.path.join(self.base_path,SAVES_FILE)

    def load_saves(self):
        try:
            if os.path.exists(self._saves_path()):
                with open(self._saves_path(),'r') as f: self.save_slots_list=json.load(f)
            else: self.save_slots_list=[]
        except Exception: self.save_slots_list=[]

    def _write_saves(self):
        try:
            with open(self._saves_path(),'w') as f: json.dump(self.save_slots_list,f,indent=2)
        except Exception: pass

    def _save_exists(self): return len(self.save_slots_list)>0

    def _collect_game_data(self, name):
        now=pygame.time.get_ticks()
        return {'slot_name':name,'timestamp':datetime.now().strftime("%Y-%m-%d  %H:%M"),
                'score':self.score,'lives':self.lives,'nukes':self.nukes,'shields':self.shields,
                'weapon':self.weapon,'weapon_tier':self.weapon_tier,'stage':self.stage,
                'distance':round(self.distance,4),'ghost_fires':self.ghost_fires,
                'dev_weapons_maxed':self.dev_weapons_maxed,
                'keyword_progress':{k:list(v) for k,v in self.keyword_progress.items()},
                'zapp_active':self.zapp_active,
                'zapp_cooldown_rem':max(0,self.zapp_cooldown_timer-now),
                'drone_rem':max(0,self.drone_timer-now),'warp_rem':max(0,self.warp_timer-now),
                'shield_rem':max(0,self.shield_timer-now),
                'shield_active':self.shield_active,'shield_hp':self.shield_hp}

    def save_to_slot(self, name, overwrite_idx=None):
        data=self._collect_game_data(name)
        if overwrite_idx is not None and 0<=overwrite_idx<len(self.save_slots_list):
            self.save_slots_list[overwrite_idx]=data
        else:
            self.save_slots_list.append(data)
        self._write_saves(); self.save_flash=pygame.time.get_ticks()+1200

    def load_from_slot(self, idx):
        if idx<0 or idx>=len(self.save_slots_list): return False
        data=self.save_slots_list[idx]
        try:
            self.reset_game(False); now=pygame.time.get_ticks()
            self.score=int(data.get('score',0)); self.display_score=self.score
            self.lives=int(data.get('lives',3)); self.nukes=int(data.get('nukes',1))
            self.shields=int(data.get('shields',0)); self.weapon=data.get('weapon','normal')
            self.weapon_tier=int(data.get('weapon_tier',1)); self.stage=int(data.get('stage',1))
            self.distance=float(data.get('distance',0.0)); self.ghost_fires=int(data.get('ghost_fires',0))
            self.dev_weapons_maxed=bool(data.get('dev_weapons_maxed',False))
            kp=data.get('keyword_progress',{})
            for k in self.keyword_progress:
                if k in kp: self.keyword_progress[k]=list(kp[k])
            self.zapp_active=bool(data.get('zapp_active',False))
            self.zapp_cooldown_timer=now+int(data.get('zapp_cooldown_rem',0))
            self.drone_timer=now+int(data.get('drone_rem',0))
            self.warp_timer=now+int(data.get('warp_rem',0))
            self.shield_timer=now+int(data.get('shield_rem',0))
            self.shield_active=bool(data.get('shield_active',False))
            self.shield_hp=int(data.get('shield_hp',0))
            self.init_stars(self.stage); self._init_nebulas(self.stage); self._init_pulsars(self.stage)
            self.planets=[Planet(self.stage) for _ in range(3)]
            self.ship=Spaceship(); self.ship.reset(True)
            self.state=STATE_PLAYING; self.play_next_track(False); return True
        except Exception: return False

    def delete_slot(self, idx):
        if 0<=idx<len(self.save_slots_list):
            self.save_slots_list.pop(idx); self._write_saves()

    # ── Save / Load UI ────────────────────────────────────────────────────────
    def _open_save_menu(self):
        self.load_saves(); self.sm_idx=0; self.sm_confirm=False
        self.sm_overwrite_idx=None; self.state=STATE_SAVE_MENU; self.sm_origin=STATE_PAUSED

    def _open_load_menu(self):
        self.load_saves(); self.lm_idx=0; self.state=STATE_LOAD_MENU

    def _draw_slot_row(self, screen, slot, idx, sel, rx, y, rw, rh, is_new=False):
        bg=pygame.Surface((rw,rh),pygame.SRCALPHA)
        bg.fill((30,55,105,100) if sel else (12,18,36,60))
        screen.blit(bg,(rx,y))
        pygame.draw.rect(screen,CYAN if sel else (40,70,120),(rx,y,3,rh),border_radius=2)
        if sel: pygame.draw.rect(screen,(*CYAN,180),(rx,y,rw,rh),1,border_radius=3)
        if is_new:
            c=YELLOW if sel else (70,160,90)
            plus=self.menu_font.render("＋  NEW SAVE",True,c)
            screen.blit(plus,(rx+14,y+rh//2-plus.get_height()//2))
        else:
            badge_col=(0,180,200) if sel else (40,80,100)
            pygame.draw.rect(screen,badge_col,(rx+6,y+10,26,rh-20),border_radius=3)
            ni=self.info_font.render(str(idx+1),True,WHITE)
            screen.blit(ni,(rx+6+13-ni.get_width()//2,y+rh//2-ni.get_height()//2))
            nc=YELLOW if sel else (220,220,240); mc=(190,190,100) if sel else (100,110,130)
            screen.blit(self.menu_font.render(slot['slot_name'],True,nc),(rx+40,y+5))
            screen.blit(self.info_font.render(
                f"Stage {slot.get('stage',1)}     Score {slot.get('score',0):07}     {slot.get('timestamp','')}",
                True,mc),(rx+40,y+30))

    def _draw_save_menu(self):
        ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,185)); self.screen.blit(ov,(0,0))
        pw,ph=580,440; px,py=SCREEN_WIDTH//2-pw//2,SCREEN_HEIGHT//2-ph//2
        self.screen.blit(_glass_surface(pw,ph),(px,py))
        tt=self.menu_font.render("SAVE  GAME",True,CYAN); self.screen.blit(tt,(SCREEN_WIDTH//2-tt.get_width()//2,py+12))
        pygame.draw.line(self.screen,(50,80,160),(px+16,py+42),(px+pw-16,py+42),1)
        slots=self.save_slots_list; can_new=len(slots)<MAX_SAVE_SLOTS
        rows=slots+([None] if can_new else []); lh,pad=56,8; cy0=py+52; rw=pw-pad*2; rh=lh-6
        for i,slot in enumerate(rows):
            self._draw_slot_row(self.screen,slot,i,(i==self.sm_idx),px+pad,cy0+i*lh,rw,rh,is_new=(slot is None))
        if self.sm_confirm:
            cfx=px+pw//2-170; cfy=py+ph-100
            self.screen.blit(_glass_surface(340,82,(20,8,8,235),(200,60,60,130)),(cfx,cfy))
            l1=self.info_font.render("Overwrite this save?",True,YELLOW)
            l2=self.info_font.render("ENTER  confirm          ESC  cancel",True,(190,190,190))
            self.screen.blit(l1,(cfx+170-l1.get_width()//2,cfy+10))
            self.screen.blit(l2,(cfx+170-l2.get_width()//2,cfy+40))
        else:
            hints=[("↑ ↓","Navigate"),("ENTER","Save / Select"),("D / DEL","Delete"),("ESC","Back")]
            hx=px+14
            for k,v in hints:
                ki=self.info_font.render(k,True,YELLOW); vi=self.info_font.render(f"  {v}   ",True,(100,110,130))
                self.screen.blit(ki,(hx,py+ph-22)); hx+=ki.get_width()
                self.screen.blit(vi,(hx,py+ph-22)); hx+=vi.get_width()

    def _draw_load_menu(self):
        ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,185)); self.screen.blit(ov,(0,0))
        pw,ph=580,440; px,py=SCREEN_WIDTH//2-pw//2,SCREEN_HEIGHT//2-ph//2
        self.screen.blit(_glass_surface(pw,ph),(px,py))
        tt=self.menu_font.render("LOAD  GAME",True,CYAN); self.screen.blit(tt,(SCREEN_WIDTH//2-tt.get_width()//2,py+12))
        pygame.draw.line(self.screen,(50,80,160),(px+16,py+42),(px+pw-16,py+42),1)
        slots=self.save_slots_list; lh,pad=56,8; cy0=py+52; rw=pw-pad*2; rh=lh-6
        if not slots:
            msg=self.info_font.render("No saved games found.",True,(100,110,140))
            self.screen.blit(msg,(SCREEN_WIDTH//2-msg.get_width()//2,cy0+80))
        else:
            for i,slot in enumerate(slots):
                self._draw_slot_row(self.screen,slot,i,(i==self.lm_idx),px+pad,cy0+i*lh,rw,rh)
        hints=[("↑ ↓","Navigate"),("ENTER","Load"),("D / DEL","Delete"),("ESC","Back")]
        hx=px+14
        for k,v in hints:
            ki=self.info_font.render(k,True,YELLOW); vi=self.info_font.render(f"  {v}   ",True,(100,110,130))
            self.screen.blit(ki,(hx,py+ph-22)); hx+=ki.get_width()
            self.screen.blit(vi,(hx,py+ph-22)); hx+=vi.get_width()

    def _draw_save_name_entry(self):
        ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,185)); self.screen.blit(ov,(0,0))
        pw,ph=480,160; px,py=SCREEN_WIDTH//2-pw//2,SCREEN_HEIGHT//2-ph//2
        self.screen.blit(_glass_surface(pw,ph),(px,py))
        tt=self.menu_font.render("NAME THIS SAVE",True,CYAN); self.screen.blit(tt,(SCREEN_WIDTH//2-tt.get_width()//2,py+12))
        fw,fx,fy=pw-40,px+20,py+58
        pygame.draw.rect(self.screen,(20,30,55),(fx,fy,fw,36),border_radius=4)
        pygame.draw.rect(self.screen,(60,100,180),(fx,fy,fw,36),1,border_radius=4)
        cursor="|" if (pygame.time.get_ticks()//400)%2==0 else " "
        ti=self.menu_font.render(self.sm_name_input+cursor,True,WHITE); self.screen.blit(ti,(fx+8,fy+7))
        h1=self.info_font.render("Type a name  (max 16 chars)",True,(100,120,160))
        h2=self.info_font.render("ENTER  confirm       ESC  cancel",True,(100,120,160))
        self.screen.blit(h1,(SCREEN_WIDTH//2-h1.get_width()//2,py+102))
        self.screen.blit(h2,(SCREEN_WIDTH//2-h2.get_width()//2,py+120))

    # ── Screenshot ────────────────────────────────────────────────────────────
    def take_screenshot(self):
        ts=datetime.now().strftime("%Y%m%d_%H%M%S"); path=os.path.join(self.base_path,f"screenshot_{ts}.png")
        try: pygame.image.save(self.screen,path); self.screenshot_flash=pygame.time.get_ticks()+900
        except Exception: pass

    def _adjust_timers(self, offset):
        self.flare_timer+=offset; self.idle_timer+=offset; self.zapp_cooldown_timer+=offset
        self.drone_timer+=offset; self.warp_timer+=offset; self.boss_collision_cooldown+=offset
        self.shield_timer+=offset; self.last_fire+=offset; self.ship.invulnerable_until+=offset
        for bo in self.bosses:
            bo.last_move_change+=offset; bo.rage_attack_timer+=offset
            if bo.is_dying: bo.death_timer+=offset
        for en in self.enemies:
            if en.is_warship or en.is_yellow_drone: en.timer+=offset; en.last_shot+=offset

    # ── Audio ─────────────────────────────────────────────────────────────────
    def load_audio(self):
        self.music_path   = os.path.join(self.base_path,"Music")
        self.effects_path = os.path.join(self.base_path,"Effects")
        self.music_tracks = (
            [os.path.join(self.music_path,f) for f in os.listdir(self.music_path)
             if f.endswith(('.mp3','.wav'))]
            if os.path.exists(self.music_path) else [])

        boss_p = os.path.join(self.music_path,"Boss")
        self.boss_tracks = (
            [os.path.join(boss_p,f) for f in os.listdir(boss_p)
             if f.endswith(('.mp3','.wav'))]
            if os.path.exists(boss_p) else [])

        # Rage music pool — Music/Boss/Rage/
        rage_p = os.path.join(self.music_path,"Boss","Rage")
        self.rage_tracks = (
            [os.path.join(rage_p,f) for f in os.listdir(rage_p)
             if f.endswith(('.mp3','.wav'))]
            if os.path.exists(rage_p) else [])

        # Title screen music pool — Music/Titles/
        title_p = os.path.join(self.music_path,"Titles")
        self.title_tracks = (
            [os.path.join(title_p,f) for f in os.listdir(title_p)
             if f.endswith(('.mp3','.wav'))]
            if os.path.exists(title_p) else [])

        random.shuffle(self.music_tracks)
        self.stage_music_tracks = {}
        for st in (1,2,3):
            sp   = os.path.join(self.music_path,f"Stage{st}")
            pool = ([os.path.join(sp,f) for f in os.listdir(sp)
                     if f.endswith(('.mp3','.wav'))]
                    if os.path.exists(sp) else [])
            p = pool if pool else list(self.music_tracks)
            random.shuffle(p)
            self.stage_music_tracks[st] = p
        self.stage_track_idx   = {1:0,2:0,3:0,4:0}
        self.current_track_idx = 0
        self.music_stopped     = False
        pygame.mixer.music.set_volume(0.4)
        self.sounds = {}
        if os.path.exists(self.effects_path):
            mappings = {
                'shoot_normal':'Shoot1.wav',  'shoot_dual':'Shoot2.wav',
                'shoot_triple':'Shoot3.wav',  'shoot_laser':'Shoot10.wav',
                'shoot_blast':'Shoot20.wav',  'boom_normal':'Boom1.wav',
                'boom_tank':'Boom10.wav',     'boom_nuke':'Boom15.wav',
                'boom_ship':'Boom18.wav',     'hit_normal':'Hit1.wav',
                'hit_tank':'Hit11.wav',       'powerup':'PowerUp.wav',
                'game_over':'Random3.wav',    'warning':'Mutant.wav',
                'blip':'Blip.wav',            'warp':'Random1.wav',
                'zap':'Shoot25.wav',          'boss_impact':'Boom12.wav',
                'hotkey_panel':'powerUp4.wav',
            }
            for k,v in mappings.items():
                p=os.path.join(self.effects_path,v)
                if os.path.exists(p):
                    self.sounds[k]=pygame.mixer.Sound(p); self.sounds[k].set_volume(0.55)
        # Apply persisted volumes (load_settings runs after load_audio, so we re-apply there)
        # Volume sync happens in load_settings via _apply_volumes called after both are loaded

    def load_highscores(self):
        if os.path.exists(self.highscore_path):
            try:
                with open(self.highscore_path,'r') as f: self.highscores=json.load(f)
            except Exception: self.highscores=[]
        else: self.highscores=[]
        self.highscores=sorted(self.highscores,key=lambda x:x['score'],reverse=True)[:5]

    def save_highscores(self):
        try:
            self.highscores=sorted(self.highscores,key=lambda x:x['score'],reverse=True)[:5]
            with open(self.highscore_path,'w') as f: json.dump(self.highscores,f)
        except Exception: pass

    # ── Music helpers ─────────────────────────────────────────────────────────
    def play_sfx(self, key):
        """Play a sound effect if SFX is enabled."""
        if self.sfx_enabled and key in self.sounds:
            self.sounds[key].play()

    def play_title_music(self):
        """Play a random track from Music/Titles/ on the intro screen."""
        if not self.music_enabled or not self.title_tracks:
            return
        pygame.mixer.music.stop()
        pygame.mixer.music.load(random.choice(self.title_tracks))
        pygame.mixer.music.play(-1)

    def play_next_track(self, boss=False, rage=False):
        """Advance gameplay music — stage-aware, reshuffles on wrap."""
        if not self.music_enabled: return
        if rage:
            # Rage pool falls back to boss pool if folder is empty/missing
            pool = self.rage_tracks if self.rage_tracks else self.boss_tracks
            if pool:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(random.choice(pool))
                pygame.mixer.music.play()
        elif boss:
            if self.boss_tracks:
                pygame.mixer.music.load(random.choice(self.boss_tracks))
                pygame.mixer.music.play()
        else:
            st     = getattr(self,'stage',1)
            tracks = self.stage_music_tracks.get(st,self.music_tracks)
            if not tracks: return
            idx = self.stage_track_idx.get(st,0)
            if idx >= len(tracks):
                random.shuffle(tracks); idx=0
            pygame.mixer.music.load(tracks[idx]); pygame.mixer.music.play()
            self.stage_track_idx[st] = idx+1

    def create_explosion(self, x, y, color, count=15, speed=1.0):
        for _ in range(count): self.particles.append(Particle(x,y,color,speed=speed))

    # ── Menu overlays ─────────────────────────────────────────────────────────
    def draw_menu_overlay(self, title, options, color, small_title=False):
        self.menu_count=len(options)
        ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,180)); self.screen.blit(ov,(0,0))

        # Title — prominent at top
        t=self.title_font.render(title,True,color)
        self.screen.blit(t,(SCREEN_WIDTH//2-t.get_width()//2, MENU_TITLE_Y))

        # Menu — vertically centred in the middle zone
        zone_top, zone_bot = MENU_ZONE_TOP, MENU_ZONE_BOT
        menu_item_h = MENU_ITEM_H
        block_h = len(options) * menu_item_h
        menu_top = zone_top + (zone_bot - zone_top - block_h) // 2
        menu_bot = menu_top + block_h

        # Framing lines — equal gap above and below the menu block
        gap = MENU_FRAME_GAP
        pygame.draw.line(self.screen,(40,60,100),(80, menu_top-gap),(SCREEN_WIDTH-80, menu_top-gap),1)
        pygame.draw.line(self.screen,(40,60,100),(80, menu_bot+gap),(SCREEN_WIDTH-80, menu_bot+gap),1)
        for i,opt in enumerate(options):
            c=YELLOW if i==self.menu_idx else WHITE
            f=self.info_font if (self.state==STATE_CONTINUE or "YES" in opt) else self.menu_font
            img=f.render(("> "+opt+" <") if i==self.menu_idx else opt,True,c)
            self.screen.blit(img,(SCREEN_WIDTH//2-img.get_width()//2, menu_top+i*menu_item_h))

        # Top Pilots — anchored to lower screen
        if self.state in (STATE_INTRO,STATE_GAME_OVER):
            hy = MENU_SCORES_Y
            th=self.info_font.render("--- Top Pilots ---",True,CYAN)
            self.screen.blit(th,(SCREEN_WIDTH//2-th.get_width()//2, hy))
            for i,hs in enumerate(self.highscores[:5]):
                row=self.info_font.render(f"{i+1}.  {hs['name']}  {hs['score']:07}",True,WHITE)
                self.screen.blit(row,(SCREEN_WIDTH//2-row.get_width()//2, hy+20+i*20))
            # Easter eggs
            names = [hs['name'].upper() for hs in self.highscores]
            has_fuck = 'FUCK' in names
            has_nick = 'NICK' in names
            egg_text = None
            if has_fuck and has_nick:
                egg_text = "Look man... i'm not happy about it" if (pygame.time.get_ticks()//5000)%2==0 else "It is: Nikos Georgousis"
            elif has_fuck:
                egg_text = "Look man... i'm not happy about it"
            elif has_nick:
                egg_text = "It is: Nikos Georgousis"
            if egg_text:
                eg = self.info_font.render(egg_text, True, (180, 180, 60))
                self.screen.blit(eg, (SCREEN_WIDTH//2 - eg.get_width()//2, hy + 120))

        if self.state == STATE_INTRO:
            music_on = pygame.mixer.music.get_busy()
            m_col  = (60,200,80) if music_on else (180,60,60)
            m_hint = self.info_font.render("M  Music " + ("ON" if music_on else "OFF"), True, m_col)
            self.screen.blit(m_hint,(10,HUD_BOTTOM))
            pulse_a = int(160 + 95 * abs(math.sin(pygame.time.get_ticks() * 0.0015)))
            cr_surf = self.info_font.render("v0.18      Created by Nikos Georgousis", True, WHITE)
            cr_alpha = pygame.Surface(cr_surf.get_size(), pygame.SRCALPHA)
            cr_alpha.fill((0,0,0,0)); cr_alpha.blit(cr_surf,(0,0)); cr_alpha.set_alpha(pulse_a)
            self.screen.blit(cr_alpha,(SCREEN_WIDTH - cr_surf.get_width() - 10, HUD_BOTTOM))


    def _draw_settings_menu(self):
        self.menu_count=5
        ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,195)); self.screen.blit(ov,(0,0))
        t=self.title_font.render("SETTINGS",True,CYAN); self.screen.blit(t,(SCREEN_WIDTH//2-t.get_width()//2,SETT_TITLE_Y))
        sep_y = SETT_TITLE_Y + t.get_height() + 6
        pygame.draw.line(self.screen,DARK_GRAY,(SCREEN_WIDTH//5, sep_y),(SCREEN_WIDTH*4//5, sep_y),1)

        w,h = RESOLUTIONS[self.resolution_idx]
        res_str = "%dx%d" % (w, h)
        row_defs=[
            ("SFX",        self.sfx_enabled,        self.sfx_volume,  True,  False),
            ("MUSIC",      self.music_enabled,       self.music_volume,True,  False),
            ("TRAJECTORY", self.trajectory_enabled,  None,             False, False),
            ("RESOLUTION", None,                     None,             False, True),
            ("BACK",       None,                     None,             False, False),
        ]
        row_base = SETT_ROW_BASE   # ~144 @ 600
        row_step = SETT_ROW_STEP   # ~90 @ 600
        # With 5 rows and sliders on rows 0+1, compress step slightly so BACK fits
        row_step5 = SCREEN_HEIGHT * 12 // 100
        y_positions = [row_base + i*row_step5 for i in range(5)]
        for i,(label,enabled,vol,has_slider,is_res) in enumerate(row_defs):
            y=y_positions[i]; sel=(i==self.menu_idx); sc=YELLOW if sel else WHITE
            px=">  " if sel else "   "; sx="  <" if sel else ""
            if label=="BACK":
                bk=self.menu_font.render(f"{px}BACK{sx}",True,sc)
                self.screen.blit(bk,(SCREEN_WIDTH//2-bk.get_width()//2,y))
            elif is_res:
                lbl=self.menu_font.render(f"{px}RESOLUTION:",True,sc)
                vl =self.menu_font.render(f"  {res_str}{sx}",True,CYAN if sel else WHITE)
                tot=lbl.get_width()+vl.get_width(); lx=SCREEN_WIDTH//2-tot//2
                self.screen.blit(lbl,(lx,y)); self.screen.blit(vl,(lx+lbl.get_width(),y))
            else:
                val_str="ON" if enabled else "OFF"
                vc=GREEN if enabled else RED
                lbl=self.menu_font.render(f"{px}{label}:",True,sc)
                vl =self.menu_font.render(f"  {val_str}{sx}",True,vc)
                tot=lbl.get_width()+vl.get_width(); lx=SCREEN_WIDTH//2-tot//2
                self.screen.blit(lbl,(lx,y)); self.screen.blit(vl,(lx+lbl.get_width(),y))
                if has_slider:
                    bw=220; bh=8; bx=SCREEN_WIDTH//2-bw//2; by=y+34
                    pygame.draw.rect(self.screen,DARK_GRAY,(bx,by,bw,bh),border_radius=4)
                    fill_w=int(bw*vol)
                    bar_col=(GREEN if vol>0.5 else (YELLOW if vol>0.2 else RED)) if enabled else (50,50,50)
                    if fill_w>0: pygame.draw.rect(self.screen,bar_col,(bx,by,fill_w,bh),border_radius=4)
                    pygame.draw.rect(self.screen,(80,80,100),(bx,by,bw,bh),1,border_radius=4)
                    for t in range(1,10):
                        tx=bx+int(bw*t*0.1)
                        pygame.draw.line(self.screen,(40,40,60),(tx,by),(tx,by+bh))
                    kx=bx+fill_w; pygame.draw.circle(self.screen,WHITE if sel else (160,160,180),(kx,by+bh//2),6)
                    pct=self.info_font.render(f"{int(vol*100)}%",True,sc if sel else (120,120,140))
                    self.screen.blit(pct,(bx+bw+8,by-2))

        hint=self.info_font.render("ENTER/SPACE toggle  |  LEFT/RIGHT adjust  |  ESC back",True,DARK_GRAY)
        self.screen.blit(hint,(SCREEN_WIDTH//2-hint.get_width()//2, HUD_BOTTOM))

    def handle_highscore_transition(self):
        is_hs=(self.score>=2000 and (len(self.highscores)<5 or self.score>self.highscores[-1]['score']))
        self.state=STATE_NAME_ENTRY if is_hs else STATE_GAME_OVER; self.menu_idx=0
        if self.state==STATE_GAME_OVER: self.menu_count=2

    def trigger_keyword(self, word):
        self.play_sfx('powerup')
        if word=="LIFE":   self.lives=min(6,self.lives+1); self.keyword_progress[word]=[False]*len(word)
        elif word=="ZAPP":
            self.zapp_y=SCREEN_HEIGHT; self.zapp_active=True
            self.zapp_cooldown_timer=pygame.time.get_ticks()+16000
            self.zapp_ready_timer=pygame.time.get_ticks()+10000
            self.play_sfx('zap')
        elif word=="BOOST":self.warp_timer=pygame.time.get_ticks()+WARP_DURATION_MS; self.keyword_progress[word]=[False]*len(word); self.play_sfx('warp')

    def reset_game(self, full=False):
        self.bullets=[]; self.enemies=[]; self.powerups=[]; self.letters=[]; self.meteorites=[]
        self.boss_bullets=[]; self.mortars=[]; self.paused=False; self.stage_cleared=False; self.pause_time=0
        self.ship_ready_time=pygame.time.get_ticks(); self.music_stopped=False
        self.idle_timer=pygame.time.get_ticks(); self.last_ship_pos=(0,0); self.unbreakable_hits=0
        self.drone_timer=0; self.ghost_fires=0; self.death_timer=0; self.killer_enemy=None
        self.zapp_y=None; self.warp_timer=0
        self.keyword_progress={"LIFE":[False]*4,"ZAPP":[False]*4,"BOOST":[False]*5}
        self.bosses=[]; self.boss_mode=False; self.boss_intro_done=False
        self.flare_timer=0; self.victory_timer=0; self.boss_hits_received=0
        self.zapp_active=False; self.zapp_cooldown_timer=0; self.super_laser_toggle=False
        self.weapon_tier=1; self.impact_flash=0; self.hit_shockwave=0
        self.entry_name=[0,0,0,0]; self.entry_idx=0; self.continue_timer=0
        self.boss_collision_cooldown=0; self.shields=0; self.shield_active=False
        self.shield_hp=0; self.shield_timer=0; self.esc_pause_start=0
        self.hud_jitter=0; self.hud_visible=True; self.save_flash=0; self.show_hotkeys=False
        self.settings_origin=STATE_INTRO
        self.rage_flash_timer=0; self.stage_briefing_timer=0
        self.shield_hint_timer=0; self.shield_hint_count=0
        self.zapp_ready_timer=0; self.boss_rage_active=False
        self.yellow_drone_timer=0  # stage 4: next yellow drone spawn time
        self.warship_spawned_count=0  # stage 4: counts red warships spawned, yellow drone every 7th
        if full:
            self.ship,self.score,self.lives,self.nukes=Spaceship(),0,3,1
            self.weapon,self.stage,self.frames='normal',1,0
            self.distance,self.target_distance=0.0,10.0
            self.display_score=0; self.dev_weapons_maxed=False
            random.shuffle(self.music_tracks)
            for pool in self.stage_music_tracks.values(): random.shuffle(pool)
            self.stage_track_idx={1:0,2:0,3:0,4:0}; self.current_track_idx=0
        self.stage_briefing_timer=pygame.time.get_ticks()+3500
        if self.state==STATE_PLAYING: self.play_next_track()

    def trigger_victory(self):
        self.bullets=[]; self.enemies=[]; self.boss_bullets=[]; self.mortars=[]; self.powerups=[]; self.letters=[]; self.meteorites=[]
        self.state=STATE_VICTORY; self.victory_timer=pygame.time.get_ticks()
        self.boss_rage_active=False
        pygame.mixer.music.stop()
        sp=os.path.join(self.music_path,"Stage")
        if os.path.exists(sp):
            tracks=[os.path.join(sp,f) for f in os.listdir(sp) if any(x in f for x in ("Achievement","Cleared"))]
            if tracks and self.music_enabled: pygame.mixer.music.load(random.choice(tracks)); pygame.mixer.music.play()

    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    def run(self):
        while True:
            dt=self.clock.tick(60); now=pygame.time.get_ticks()
            speed_mult=(3.0 if self.warp_timer>now else
                        (0.2 if self.boss_mode and not self.boss_intro_done else 1.0))

            if self.state==STATE_PLAYING and not self.paused and not pygame.mixer.music.get_busy():
                self.play_next_track(self.boss_mode, rage=self.boss_rage_active)

            off=((random.randint(-self.shake,self.shake),random.randint(-self.shake,self.shake))
                 if self.shake>0 else (0,0))
            if self.shake>0: self.shake-=1
            self.screen.fill(BLACK)

            if self.display_score<self.score:
                self.display_score=min(self.score,self.display_score+max(1,(self.score-self.display_score)//6))

            for s in self.stars_bg:
                s[1]=(s[1]+s[2]*speed_mult*0.20)%SCREEN_HEIGHT
                pygame.draw.circle(self.screen,s[3],(int(s[0]+off[0]),int(s[1]+off[1])),s[4])
            if self.pulsars: self._draw_pulsars(off)
            self._draw_nebulas(off)
            for s in self.stars_mid:
                s[1]=(s[1]+s[2]*speed_mult*0.50)%SCREEN_HEIGHT
                pygame.draw.circle(self.screen,s[3],(int(s[0]+off[0]),int(s[1]+off[1])),s[4])
            for p in self.planets: p.update(speed_mult,self.stage); p.draw(self.screen,off)
            for s in self.stars_fg:
                s[1]=(s[1]+s[2]*speed_mult*1.00)%SCREEN_HEIGHT
                pygame.draw.circle(self.screen,s[3],(int(s[0]+off[0]),int(s[1]+off[1])),s[4])

            # =================================================================
            # EVENTS
            # =================================================================
            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_F12: self.pending_screenshot=True

                    # ---------------------------------------------------------
                    # STATE_PLAYING
                    # ---------------------------------------------------------
                    if self.state==STATE_PLAYING:
                        if e.key==pygame.K_ESCAPE:
                            self.state=STATE_PAUSED; self.menu_idx=0; self.menu_count=4
                            self.esc_pause_start=now; self.play_sfx('blip')
                        elif e.key==pygame.K_h:
                            self.hud_visible=not self.hud_visible
                        elif e.key==pygame.K_BACKQUOTE:
                            self.drone_timer=now+DRONE_DURATION_MS; self.play_sfx('powerup')
                        elif e.key==pygame.K_c and self.shields>0 and not self.shield_active:
                            self.shields-=1; self.shield_active=True; self.shield_hp=3
                            self.shield_timer=now+20000; self.play_sfx('warp')
                        elif e.key==pygame.K_x and self.nukes>0:
                            self.nukes-=1; self.shake=20
                            self.create_explosion(self.ship.x+35,self.ship.y,WHITE,50); self.play_sfx('boom_nuke')
                            if any(self.ship.rect.colliderect(p.rect) for p in self.planets):
                                self.powerups.append(PowerUp(self.ship.x+35,self.ship.y,'ghost'))
                            for en in self.enemies: en.hit()
                            self.enemies=[en for en in self.enemies if not (en.hp<=0 and not en.is_unbreakable)]
                        elif e.key==pygame.K_z and self.zapp_active and now>self.zapp_cooldown_timer:
                            self.zapp_y=SCREEN_HEIGHT; self.play_sfx('zap'); self.zapp_cooldown_timer=now+16000
                        else:
                            shift=pygame.key.get_mods()&(pygame.KMOD_LSHIFT|pygame.KMOD_RSHIFT)
                            if shift:
                                if e.key==pygame.K_F1:
                                    self.lives=6; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F2:
                                    self.nukes+=3; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F3:
                                    self.distance=9.0; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F4:
                                    for _ in range(3):
                                        self.screen.fill(WHITE); pygame.display.flip(); pygame.time.delay(50)
                                        self.screen.fill(BLACK); pygame.display.flip(); pygame.time.delay(50)
                                    self.stage+=1; self.distance=0
                                    self.init_stars(self.stage); self._init_nebulas(self.stage); self._init_pulsars(self.stage)
                                    self.planets=[Planet(self.stage) for _ in range(3)]
                                    self.reset_game(False); self.ship.reset(True)
                                    self.state=STATE_PLAYING; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F5:
                                    self.distance=9.95; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F6:
                                    self.dev_weapons_maxed=True
                                    if self.weapon=='laser': self.weapon='super_laser'
                                    self.weapon_tier=2; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F7:
                                    self.weapon='super_laser'; self.weapon_tier=2; self.play_sfx('hotkey_panel')
                                elif e.key==pygame.K_F8:
                                    cycle=['dual','triple','blast','laser']
                                    idx=(cycle.index(self.weapon)+1)%len(cycle) if self.weapon in cycle else 0
                                    self.weapon=cycle[idx]; self.weapon_tier=1; self.play_sfx('hotkey_panel')

                    # ---------------------------------------------------------
                    # STATE_PAUSED
                    # ---------------------------------------------------------
                    elif self.state==STATE_PAUSED:
                        if e.key==pygame.K_h:
                            self.show_hotkeys=not self.show_hotkeys; self.play_sfx('hotkey_panel')
                        elif e.key==pygame.K_ESCAPE:
                            self.show_hotkeys=False; self.state=STATE_PLAYING
                            if self.esc_pause_start>0: self._adjust_timers(now-self.esc_pause_start); self.esc_pause_start=0
                            self.menu_count=4
                        elif not self.show_hotkeys:
                            if e.key==pygame.K_UP:   self.menu_idx=(self.menu_idx-1)%self.menu_count; self.play_sfx('blip')
                            elif e.key==pygame.K_DOWN: self.menu_idx=(self.menu_idx+1)%self.menu_count; self.play_sfx('blip')
                            elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                                self.play_sfx('blip')
                                if self.menu_idx==0:
                                    self.state=STATE_PLAYING
                                    if self.esc_pause_start>0: self._adjust_timers(now-self.esc_pause_start); self.esc_pause_start=0
                                elif self.menu_idx==1: self._open_save_menu()
                                elif self.menu_idx==2:
                                    self.settings_origin=STATE_PAUSED; self.state=STATE_SETTINGS; self.menu_idx=0; self.menu_count=5
                                else:
                                    self.state=STATE_INTRO; self.menu_count=3
                                    pygame.mixer.music.stop(); self.play_title_music()

                    # ---------------------------------------------------------
                    # STATE_SAVE_MENU
                    # ---------------------------------------------------------
                    elif self.state==STATE_SAVE_MENU:
                        slots=self.save_slots_list; can_new=len(slots)<MAX_SAVE_SLOTS
                        total=len(slots)+(1 if can_new else 0)
                        if e.key==pygame.K_ESCAPE:
                            if self.sm_confirm: self.sm_confirm=False
                            else: self.state=STATE_PAUSED; self.play_sfx('blip')
                        elif e.key==pygame.K_UP:
                            self.sm_idx=(self.sm_idx-1)%total; self.sm_confirm=False; self.play_sfx('blip')
                        elif e.key==pygame.K_DOWN:
                            self.sm_idx=(self.sm_idx+1)%total; self.sm_confirm=False; self.play_sfx('blip')
                        elif e.key in (pygame.K_DELETE,pygame.K_d) and not self.sm_confirm:
                            if self.sm_idx<len(slots):
                                self.delete_slot(self.sm_idx); self.sm_idx=max(0,self.sm_idx-1); self.play_sfx('blip')
                        elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                            if self.sm_confirm:
                                self.save_to_slot(slots[self.sm_overwrite_idx]['slot_name'],self.sm_overwrite_idx)
                                self.sm_confirm=False; self.play_sfx('powerup'); self.state=STATE_PAUSED
                            else:
                                is_new_slot=can_new and self.sm_idx==len(slots)
                                if is_new_slot:
                                    self.sm_name_input=""; self.sm_overwrite_idx=None; self.state=STATE_SAVE_NAME; self.play_sfx('blip')
                                else:
                                    self.sm_overwrite_idx=self.sm_idx; self.sm_confirm=True; self.play_sfx('blip')

                    # ---------------------------------------------------------
                    # STATE_SAVE_NAME
                    # ---------------------------------------------------------
                    elif self.state==STATE_SAVE_NAME:
                        if e.key==pygame.K_ESCAPE:
                            self.state=STATE_SAVE_MENU; self.play_sfx('blip')
                        elif e.key==pygame.K_BACKSPACE:
                            self.sm_name_input=self.sm_name_input[:-1]
                        elif e.key in (pygame.K_RETURN,pygame.K_KP_ENTER):
                            name=self.sm_name_input.strip() or "Unnamed"
                            self.save_to_slot(name,self.sm_overwrite_idx); self.play_sfx('powerup'); self.state=STATE_PAUSED
                        else:
                            ch=e.unicode
                            if ch and len(self.sm_name_input)<16 and ch.isprintable(): self.sm_name_input+=ch

                    # ---------------------------------------------------------
                    # STATE_LOAD_MENU
                    # ---------------------------------------------------------
                    elif self.state==STATE_LOAD_MENU:
                        slots=self.save_slots_list; total=max(1,len(slots))
                        if e.key==pygame.K_ESCAPE:
                            self.state=STATE_INTRO; self.menu_count=3; self.play_sfx('blip')
                        elif e.key==pygame.K_UP:   self.lm_idx=(self.lm_idx-1)%total; self.play_sfx('blip')
                        elif e.key==pygame.K_DOWN:  self.lm_idx=(self.lm_idx+1)%total; self.play_sfx('blip')
                        elif e.key in (pygame.K_DELETE,pygame.K_d) and slots:
                            self.delete_slot(self.lm_idx); self.lm_idx=max(0,self.lm_idx-1); self.play_sfx('blip')
                        elif e.key in (pygame.K_RETURN,pygame.K_SPACE) and slots:
                            if self.load_from_slot(self.lm_idx): self.play_sfx('powerup')

                    # ---------------------------------------------------------
                    # STATE_NAME_ENTRY
                    # ---------------------------------------------------------
                    elif self.state==STATE_NAME_ENTRY:
                        if e.key==pygame.K_UP:
                            self.entry_name[self.entry_idx]=(self.entry_name[self.entry_idx]+1)%len(ALLOWED_CHARS); self.play_sfx('blip')
                        elif e.key==pygame.K_DOWN:
                            self.entry_name[self.entry_idx]=(self.entry_name[self.entry_idx]-1)%len(ALLOWED_CHARS); self.play_sfx('blip')
                        elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                            self.play_sfx('blip'); self.entry_idx+=1
                            if self.entry_idx>3:
                                name="".join([ALLOWED_CHARS[i] for i in self.entry_name])
                                self.highscores.append({"name":name,"score":self.score})
                                self.save_highscores(); self.load_highscores(); self.state=STATE_GAME_OVER; self.menu_count=2
                        elif e.key==pygame.K_BACKSPACE: self.entry_idx=max(0,self.entry_idx-1); self.play_sfx('blip')

                    # ---------------------------------------------------------
                    # STATE_SETTINGS
                    # ---------------------------------------------------------
                    elif self.state==STATE_SETTINGS:
                        if e.key==pygame.K_UP:   self.menu_idx=(self.menu_idx-1)%self.menu_count; self.play_sfx('blip')
                        elif e.key==pygame.K_DOWN: self.menu_idx=(self.menu_idx+1)%self.menu_count; self.play_sfx('blip')
                        elif e.key in (pygame.K_LEFT,pygame.K_RIGHT):
                            delta=0.1 if e.key==pygame.K_RIGHT else -0.1
                            if self.menu_idx==0:   # SFX slider
                                self.sfx_volume=round(max(0.0,min(1.0,self.sfx_volume+delta)),2)
                                self.sfx_enabled=(self.sfx_volume>0)
                                if self.sfx_enabled: self.sfx_volume_saved=self.sfx_volume
                                for snd in self.sounds.values(): snd.set_volume(self.sfx_volume)
                                self.play_sfx('blip'); self.save_settings()
                            elif self.menu_idx==1: # MUSIC slider
                                self.music_volume=round(max(0.0,min(1.0,self.music_volume+delta)),2)
                                self.music_enabled=(self.music_volume>0)
                                if self.music_enabled: self.music_volume_saved=self.music_volume
                                else: pygame.mixer.music.stop()
                                pygame.mixer.music.set_volume(self.music_volume)
                                self.play_sfx('blip'); self.save_settings()
                            elif self.menu_idx==3: # RESOLUTION cycle
                                step=1 if e.key==pygame.K_RIGHT else -1
                                self.resolution_idx=(self.resolution_idx+step)%len(RESOLUTIONS)
                                self._apply_resolution(); self.play_sfx('blip')
                        elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                            if self.menu_idx==0:   # SFX toggle
                                if self.sfx_enabled:
                                    self.sfx_volume_saved=self.sfx_volume; self.sfx_volume=0.0
                                    self.sfx_enabled=False
                                    for snd in self.sounds.values(): snd.set_volume(0.0)
                                else:
                                    self.sfx_volume=self.sfx_volume_saved if self.sfx_volume_saved>0 else 0.55
                                    self.sfx_enabled=True
                                    for snd in self.sounds.values(): snd.set_volume(self.sfx_volume)
                                self.play_sfx('blip'); self.save_settings()
                            elif self.menu_idx==1: # MUSIC toggle
                                if self.music_enabled:
                                    self.music_volume_saved=self.music_volume; self.music_volume=0.0
                                    self.music_enabled=False; pygame.mixer.music.stop()
                                else:
                                    self.music_volume=self.music_volume_saved if self.music_volume_saved>0 else 0.4
                                    self.music_enabled=True
                                    pygame.mixer.music.set_volume(self.music_volume)
                                self.play_sfx('blip'); self.save_settings()
                            elif self.menu_idx==2:
                                self.trajectory_enabled=not self.trajectory_enabled; self.save_settings(); self.play_sfx('blip')
                            elif self.menu_idx==3: # RESOLUTION cycle (ENTER also cycles)
                                self.resolution_idx=(self.resolution_idx+1)%len(RESOLUTIONS)
                                self._apply_resolution(); self.play_sfx('blip')
                            else: # BACK (idx 4)
                                self.play_sfx('blip'); self.state=self.settings_origin; self.menu_idx=0
                                self.menu_count=3 if self.settings_origin==STATE_INTRO else 4
                        elif e.key==pygame.K_ESCAPE:
                            self.play_sfx('blip'); self.state=self.settings_origin; self.menu_idx=0
                            self.menu_count=3 if self.settings_origin==STATE_INTRO else 4

                    # ---------------------------------------------------------
                    # OTHER MENU STATES  (INTRO, GAME_OVER, CLEARED, CONTINUE)
                    # ---------------------------------------------------------
                    elif self.state in (STATE_INTRO,STATE_GAME_OVER,STATE_CLEARED,STATE_CONTINUE):
                        # M key — title music toggle (INTRO only)
                        if e.key==pygame.K_m and self.state==STATE_INTRO:
                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.stop()
                            else:
                                self.play_title_music()

                        if e.key==pygame.K_UP:   self.menu_idx=(self.menu_idx-1)%self.menu_count; self.play_sfx('blip')
                        if e.key==pygame.K_DOWN:  self.menu_idx=(self.menu_idx+1)%self.menu_count; self.play_sfx('blip')
                        if e.key in (pygame.K_RETURN,pygame.K_SPACE):
                            self.play_sfx('blip')
                            if self.state==STATE_INTRO:
                                if self._save_exists():
                                    # 0=START 1=LOAD 2=SETTINGS 3=QUIT
                                    if   self.menu_idx==0: self.state=STATE_PLAYING; self.reset_game(True)
                                    elif self.menu_idx==1: self._open_load_menu()
                                    elif self.menu_idx==2:
                                        self.settings_origin=STATE_INTRO; self.state=STATE_SETTINGS; self.menu_idx=0; self.menu_count=5
                                    else: pygame.quit(); sys.exit()
                                else:
                                    # 0=START 1=SETTINGS 2=QUIT
                                    if   self.menu_idx==0: self.state=STATE_PLAYING; self.reset_game(True)
                                    elif self.menu_idx==1:
                                        self.settings_origin=STATE_INTRO; self.state=STATE_SETTINGS; self.menu_idx=0; self.menu_count=5
                                    else: pygame.quit(); sys.exit()
                            elif self.state==STATE_CONTINUE:
                                if self.menu_idx==0:
                                    self.score=0; self.lives=3; self.display_score=0
                                    self.reset_game(False); self.ship.reset(True); self.state=STATE_PLAYING
                                else: self.handle_highscore_transition()
                            elif self.state in (STATE_GAME_OVER,STATE_CLEARED):
                                if self.menu_idx==0: self.state=STATE_PLAYING; self.reset_game(True)
                                else:
                                    self.state=STATE_INTRO; self.menu_count=3; self.play_title_music()

            # -----------------------------------------------------------------
            # PARTICLES
            # -----------------------------------------------------------------
            for part in self.particles[:]:
                part.update(); part.draw(self.screen)
                if part.life<=0: self.particles.remove(part)

            # =================================================================
            # PLAYING / PAUSED
            # =================================================================
            if self.state in (STATE_PLAYING,STATE_PAUSED):
                if not self.paused and self.state==STATE_PLAYING:
                    self.frames+=1
                    if self.distance<self.target_distance: self.distance+=(dt/AU_TIME_MS)*speed_mult
                    if self.distance>=BOSS_TRIGGER_AU and not self.boss_mode:
                        self.boss_mode=True; pygame.mixer.music.fadeout(2000)
                        self.bosses=[BossPlanet(BOSS_SPAWN_LEFT,0,self.stage),BossPlanet(BOSS_SPAWN_RIGHT,1,self.stage)]; self.flare_timer=now+10000
                    if self.boss_mode and all(b.alpha>=255 for b in self.bosses): self.boss_intro_done=True

                    ks=pygame.key.get_pressed(); self.ship.move(ks)
                    if not self.ship.is_entering:
                        cx_t=self.ship.x+self.ship.width//2
                        for _ in range(4 if self.warp_timer>now else 2):
                            col=random.choice([CYAN,PURPLE,WHITE]) if self.warp_timer>now else random.choice([CYAN,BLUE,WHITE])
                            self.particles.append(Particle(cx_t+random.randint(-9,9),self.ship.y+self.ship.height-4,
                                                            col,vx=random.uniform(-0.3,0.3),vy=random.uniform(2.0,4.5),speed=0.5))

                    if (self.ship.x,self.ship.y)!=self.last_ship_pos: self.idle_timer=now; self.last_ship_pos=(self.ship.x,self.ship.y)
                    if now-self.idle_timer>IDLE_LIMIT_MS and len([en for en in self.enemies if en.is_comet])<3:
                        self.enemies.append(Enemy(is_comet=True,target_pos=(self.ship.x+35,self.ship.y+40))); self.idle_timer=now; self.play_sfx('warning')
                    # Stage 4: yellow drone spawns every 7th red warship, only if warship on screen
                    if not self.ship.is_entering and ks[pygame.K_SPACE]: self.fire()

                    sp=(0.02+self.stage*0.006)*(1.3 if self.stage==2 else 1.0)
                    if self.stage==2 and self.distance>=5.0: sp*=1.2
                    sp*=(1.3 if self.distance>=8.0 else (1.2 if self.distance>=6.0 else 1.0))
                    if random.random()<sp*speed_mult and not self.boss_mode:
                        if self.stage in (2,3,4) and random.random()<0.03:
                            self.enemies.append(Enemy(is_warship=True,stage=self.stage))
                            if self.stage==4:
                                self.warship_spawned_count+=1
                                if self.warship_spawned_count%7==0 and not any(en.is_yellow_drone for en in self.enemies) and any(en.is_warship for en in self.enemies):
                                    self.enemies.append(Enemy(is_yellow_drone=True,stage=4))
                        elif random.random()<0.05 and not any(en.is_unbreakable for en in self.enemies):
                            self.enemies.append(Enemy(is_unbreakable=True,stage=self.stage))
                        elif self.stage==3 and random.random()<0.30:
                            self.enemies.append(Enemy(is_angled=True,stage=3))
                        elif self.stage==4 and random.random()<0.60:
                            self.enemies.append(Enemy(is_angled=True,stage=4))
                        elif self.stage>=3 and random.random()<0.12:
                            self.meteorites.append(Meteorite(stage=self.stage))
                        else:
                            self.enemies.append(Enemy(is_tank=random.random()<0.12,stage=self.stage))

                    if self.shield_active and now>self.shield_timer: self.shield_active=False; self.shield_hp=0

                    if self.zapp_y is not None:
                        self.zapp_y-=5; pygame.draw.rect(self.screen,WHITE,(0,self.zapp_y,SCREEN_WIDTH,20))
                        for b in self.bosses:
                            if not b.is_dying and b.rect.colliderect(pygame.Rect(0,self.zapp_y,SCREEN_WIDTH,20)): b.hp-=0.5
                        if self.zapp_y<-20: self.zapp_y=None

                    if self.boss_mode:
                        active=[b for b in self.bosses if not b.is_dying]
                        if len(active)==2 and active[0].rect.colliderect(active[1].rect) and now>self.boss_collision_cooldown:
                            self.play_sfx('boss_impact'); self.shake=15; self.boss_collision_cooldown=now+2000
                            pygame.draw.rect(self.screen,WHITE,(0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
                            self.boss_bullets.append(BossProjectile(active[0].x,active[0].y,0,8,40,WHITE))
                            comets=len([en for en in self.enemies if en.is_comet])
                            for _ in range(min(3,3-comets)): self.enemies.append(Enemy(is_comet=True,target_pos=(self.ship.x+35,self.ship.y+40)))
                            for b in active: b.vx*=-1; b.x+=b.vx*10
                        if active and now>self.flare_timer-1500:
                            if (now//100%2==0):
                                fb=random.choice(active); pygame.draw.circle(self.screen,WHITE,fb.rect.center,fb.radius+10,5)
                        if now>self.flare_timer and active:
                            b=random.choice(active); b.shake_timer=90; self.flare_timer=now+10000
                            for a in range(0,360,15):
                                rad=math.radians(a); self.boss_bullets.append(BossProjectile(b.x,b.y,math.cos(rad)*4,math.sin(rad)*4,15,ORANGE))

                    for b in self.bullets[:]:
                        b.update(speed_mult); b.draw(self.screen)
                        if b.y<-100 or b.y>SCREEN_HEIGHT+100: self.bullets.remove(b); continue
                        for en in self.enemies[:]:
                            if en.rect.colliderect(b.rect):
                                il='laser' in b.w_key
                                if not il and b in self.bullets: self.bullets.remove(b)
                                self.create_explosion(b.x,b.y,b.config['color'],5)
                                self.play_sfx('hit_tank' if (en.is_tank or en.is_unbreakable or en.is_comet or en.is_warship or en.is_yellow_drone) else 'hit_normal')
                                if en.is_unbreakable: self.unbreakable_hits+=1
                                elif en.is_tank:
                                    if self.unbreakable_hits<10: self.unbreakable_hits=0
                                else: self.unbreakable_hits=0
                                if en.hit():
                                    self.create_explosion(en.x,en.y,en.color,20)
                                    self.play_sfx('boom_tank' if en.is_tank else 'boom_normal')
                                    if en.is_yellow_drone:
                                        self.score+=200; self.powerups.append(PowerUp(en.x,en.y,'ghost'))
                                        self.enemies.remove(en)
                                        if not il: break
                                        continue
                                    self.score+=150 if en.is_tank else 25
                                    if en.is_tank and self.unbreakable_hits>=10:
                                        self.powerups.append(PowerUp(en.x,en.y,'drone')); self.unbreakable_hits=0
                                    if random.random()<0.1:
                                        _all_chars=list({c for w in self.keyword_progress for c in w})
                                        self.letters.append(LetterItem(en.x,en.y,random.choice(_all_chars)))
                                    if random.random()<0.18:
                                        wdrop = 0.45 if self.stage==4 else 0.8
                                        pt=('nuke' if random.random()<0.2 else (random.choice(list(WEAPONS.keys())[1:5]) if random.random()<wdrop else 'shield'))
                                        self.powerups.append(PowerUp(en.x,en.y,pt))
                                    self.enemies.remove(en)
                                if not il: break
                        for bo in self.bosses[:]:
                            if not bo.is_dying and bo.rect.colliderect(b.rect):
                                il='laser' in b.w_key
                                if not il and b in self.bullets: self.bullets.remove(b)
                                bo.hp-=1; self.boss_hits_received+=1; bo.shake_timer=5; self.play_sfx('hit_tank')
                                if self.boss_hits_received%60==0: self.powerups.append(PowerUp(bo.x,bo.y,random.choice(list(WEAPONS.keys())[1:5])))
                                if self.boss_hits_received%120==0: self.powerups.append(PowerUp(bo.x,bo.y,'nuke'))
                                if bo.hp<=0:
                                    bo.is_dying=True; bo.death_timer=now; self.score+=5000
                                    rem=[b2 for b2 in self.bosses if not b2.is_dying]
                                    if len(rem)==1:
                                        rem[0].is_rage=True
                                        rem[0].hp=rem[0].max_hp   # full HP refill on rage
                                        self.rage_flash_timer=now+2500
                                        self.boss_rage_active=True
                                        self.play_next_track(rage=True)
                                if not il: break
                        for bb in self.boss_bullets[:]:
                            if bb.rect.colliderect(b.rect):
                                il='laser' in b.w_key
                                if not il and b in self.bullets: self.bullets.remove(b)
                                self.create_explosion(bb.x,bb.y,bb.color,10); self.play_sfx('blip'); self.boss_bullets.remove(bb)
                                if not il: break

                    for bo in self.bosses[:]:
                        res=bo.update()
                        if res=="shockwave": self.boss_bullets.append(BossProjectile(bo.x,bo.y,0,8,40,WHITE))
                        bo.draw(self.screen)
                        if bo.is_dying and now-bo.death_timer>1000:
                            self.create_explosion(bo.x,bo.y,RED,100,3.0); self.play_sfx('boom_ship'); self.bosses.remove(bo)
                    if self.boss_mode and not self.bosses: self.trigger_victory()

                    for en in self.enemies[:]:
                        en.update(now,(self.ship.x+35,self.ship.y+40),self.boss_bullets,self.sounds,self.particles,speed_mult,self.sfx_enabled)
                        en.draw(self.screen)
                        if (self.zapp_y is not None and en.y>self.zapp_y) or (self.warp_timer>now and en.rect.colliderect(self.ship.rect)):
                            self.create_explosion(en.x,en.y,WHITE,10); self.enemies.remove(en); self.score+=50; continue
                        if en.y>SCREEN_HEIGHT+100 or en.x<-120 or en.x>SCREEN_WIDTH+120: self.enemies.remove(en); continue
                        if not self.ship.is_invulnerable(self.warp_timer>now) and en.rect.colliderect(self.ship.rect):
                            if self.shield_active:
                                self.shield_hp-=1; self.play_sfx('hit_tank')
                                self.create_explosion(self.ship.x+35,self.ship.y+40,CYAN,10); self.enemies.remove(en)
                                if self.shield_hp<=0: self.shield_active=False
                            else:
                                self.lives-=1; self.shake=25; self.impact_flash=now+100; self.hit_shockwave=0; self.hud_jitter=now+500
                                if self.lives<=0:
                                    self.state=STATE_DEATH_SEQUENCE; self.death_timer=now; self.killer_enemy=en; pygame.mixer.music.stop()
                                else:
                                    self.create_explosion(self.ship.x+35,self.ship.y+40,RED,40); self.play_sfx('boom_ship')
                                    pygame.mixer.music.fadeout(400); self.paused=True; self.pause_time=now; self.enemies.remove(en)

                    # ── Meteorites ────────────────────────────────────────────
                    for mt in self.meteorites[:]:
                        mt.update(speed_mult, self.particles, player_pos=(self.ship.x+35, self.ship.y+40))
                        mt.draw(self.screen)
                        # Zapp / warp instant-kill
                        if (self.zapp_y is not None and mt.y>self.zapp_y) or (self.warp_timer>now and mt.rect.colliderect(self.ship.rect)):
                            self.create_explosion(mt.x,mt.y,WHITE,12); self.meteorites.remove(mt); self.score+=Meteorite.SCORE; continue
                        if mt.y>SCREEN_HEIGHT+100 or mt.x<-120 or mt.x>SCREEN_WIDTH+120: self.meteorites.remove(mt); continue
                        # Ship collision
                        if not self.ship.is_invulnerable(self.warp_timer>now) and mt.rect.colliderect(self.ship.rect):
                            if self.shield_active:
                                self.shield_hp-=1; self.play_sfx('hit_tank')
                                self.create_explosion(self.ship.x+35,self.ship.y+40,CYAN,10); self.meteorites.remove(mt)
                                if self.shield_hp<=0: self.shield_active=False
                            else:
                                self.lives-=1; self.shake=25; self.impact_flash=now+100; self.hit_shockwave=0; self.hud_jitter=now+500
                                if self.lives<=0:
                                    self.state=STATE_DEATH_SEQUENCE; self.death_timer=now; self.killer_enemy=mt; pygame.mixer.music.stop()
                                else:
                                    self.create_explosion(self.ship.x+35,self.ship.y+40,RED,40); self.play_sfx('boom_ship')
                                    pygame.mixer.music.fadeout(400); self.paused=True; self.pause_time=now; self.meteorites.remove(mt)
                        # Bullet collision — only valid if bullet hits the hot arc
                    for b in self.bullets[:]:
                        for mt in self.meteorites[:]:
                            if mt.rect.colliderect(b.rect):
                                il='laser' in b.w_key
                                if not il and b in self.bullets: self.bullets.remove(b)
                                if mt.is_hit_valid(b.x, b.y):
                                    self.create_explosion(b.x,b.y,WHITE,8); self.play_sfx('hit_tank')
                                    if mt.hit():
                                        self.create_explosion(mt.x,mt.y,(180,180,200),25)
                                        self.play_sfx('boom_tank'); self.score+=Meteorite.SCORE
                                        if random.random()<0.15:
                                            _all_chars=list({c for w in self.keyword_progress for c in w})
                                            self.letters.append(LetterItem(mt.x,mt.y,random.choice(_all_chars)))
                                        self.meteorites.remove(mt)
                                else:
                                    # Bullet deflected — spark effect only
                                    self.create_explosion(b.x,b.y,RED,4)
                                if not il: break

                    for bb in self.boss_bullets[:]:
                        bb.update(); bb.draw(self.screen)
                        if bb.rect.colliderect(self.ship.rect) and not self.ship.is_invulnerable(self.warp_timer>now):
                            if self.shield_active:
                                self.shield_hp-=1; self.play_sfx('blip')
                                if bb in self.boss_bullets: self.boss_bullets.remove(bb)
                                if self.shield_hp<=0: self.shield_active=False
                            else:
                                self.lives-=1; self.shake=25; self.impact_flash=now+100; self.hit_shockwave=0; self.hud_jitter=now+500
                                if self.lives<=0:
                                    self.state=STATE_DEATH_SEQUENCE; self.death_timer=now; pygame.mixer.music.stop()
                                else:
                                    if bb in self.boss_bullets: self.boss_bullets.remove(bb)
                                    pygame.mixer.music.fadeout(400); self.paused=True; self.pause_time=now
                        elif bb.y>SCREEN_HEIGHT+50 or bb.y<-50 or bb.x<-50 or bb.x>SCREEN_WIDTH+50:
                            if bb in self.boss_bullets: self.boss_bullets.remove(bb)

                    for p in self.powerups[:]:
                        p.update(); p.draw(self.screen)
                        if p.rect.colliderect(self.ship.rect):
                            self.play_sfx('powerup')
                            if   p.p_type=='nuke':   self.nukes+=1
                            elif p.p_type=='shield':
                                self.shields+=1
                                self.shield_hint_count=self.shields
                                self.shield_hint_timer=now+10000
                            elif p.p_type=='drone':  self.drone_timer=now+DRONE_DURATION_MS
                            elif p.p_type=='ghost':  self.ghost_fires=GHOST_MAX_FIRES
                            else:
                                if self.weapon==p.p_type:
                                    if self.weapon=='laser': self.weapon='super_laser'; self.weapon_tier=2
                                    elif self.weapon_tier<2: self.weapon_tier=2
                                    else:
                                        cx,cy=self.ship.x+35,self.ship.y
                                        self.mortars.extend([Mortar(cx,cy,-5,-5,self.weapon_tier),Mortar(cx,cy,5,-5,self.weapon_tier)]); self.play_sfx('boom_nuke')
                                elif self.weapon=='super_laser' and p.p_type=='laser':
                                    cx,cy=self.ship.x+35,self.ship.y
                                    self.mortars.extend([Mortar(cx,cy,-5,-5,2),Mortar(cx,cy,5,-5,2)]); self.play_sfx('boom_nuke')
                                else:
                                    self.weapon=p.p_type; self.weapon_tier=2 if self.dev_weapons_maxed else 1
                            self.powerups.remove(p)
                        elif p.y>SCREEN_HEIGHT: self.powerups.remove(p)

                    for m in self.mortars[:]:
                        m.update()
                        ix,iy=int(m.x),int(m.y)
                        if m.tier>=2:
                            # Tier-2+ in-flight: pulsing danger ring shows blast radius
                            blast_r=160
                            ring_a=int(60+40*abs(math.sin(m.travel*0.25)))
                            ring_surf=pygame.Surface((blast_r*2+4,blast_r*2+4),pygame.SRCALPHA)
                            pygame.draw.circle(ring_surf,(255,80,0,ring_a),(blast_r+2,blast_r+2),blast_r,2)
                            self.screen.blit(ring_surf,(ix-blast_r-2,iy-blast_r-2))
                            # Larger, brighter projectile body
                            gsurf=pygame.Surface((32,32),pygame.SRCALPHA)
                            pygame.draw.circle(gsurf,(255,60,0,80),(16,16),14)
                            self.screen.blit(gsurf,(ix-16,iy-16))
                            pygame.draw.circle(self.screen,ORANGE,(ix,iy),10)
                            pygame.draw.circle(self.screen,YELLOW,(ix,iy),6)
                            pygame.draw.circle(self.screen,WHITE, (ix,iy),3)
                        else:
                            pygame.draw.circle(self.screen,ORANGE,(ix,iy),10)
                            pygame.draw.circle(self.screen,WHITE, (ix,iy),6)
                        if m.detonated:
                            blast_r=160 if m.tier>=2 else 80
                            er=pygame.Rect(m.x-blast_r,m.y-blast_r,blast_r*2,blast_r*2)
                            if m.tier>=2:
                                # Multi-ring detonation flash
                                for ri,rc in enumerate([(255,200,0),(255,100,0),(255,255,255)]):
                                    rs=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
                                    pygame.draw.circle(rs,(*rc,120-ri*35),(ix,iy),blast_r-ri*18,6-ri)
                                    self.screen.blit(rs,(0,0))
                                self.create_explosion(m.x,m.y,ORANGE,30,4.0)
                                self.create_explosion(m.x,m.y,WHITE,20,5.0)
                                self.shake=max(self.shake,18)
                            else:
                                self.create_explosion(m.x,m.y,WHITE,12,3.0)
                            self.play_sfx('boom_nuke' if m.tier>=2 else 'boom_tank')
                            self.mortars.remove(m)
                            for en in self.enemies[:]:
                                if er.colliderect(en.rect):
                                    # Mortar is one-hit kill on everything regardless of type
                                    self.create_explosion(en.x,en.y,en.color,20)
                                    self.play_sfx('boom_tank')
                                    self.score+=150 if (en.is_tank or en.is_unbreakable) else 25
                                    self.enemies.remove(en)
                            for mt in self.meteorites[:]:
                                if er.colliderect(mt.rect):
                                    self.create_explosion(mt.x,mt.y,(180,180,200),20)
                                    self.play_sfx('boom_tank'); self.score+=Meteorite.SCORE
                                    self.meteorites.remove(mt)
                            for bb in self.boss_bullets[:]:
                                if er.collidepoint(bb.x,bb.y): self.boss_bullets.remove(bb)
                            for bo in self.bosses:
                                dmg=25 if m.tier>=2 else 10
                                if not bo.is_dying and er.colliderect(bo.rect):
                                    bo.hp-=dmg; bo.shake_timer=10

                    for l in self.letters[:]:
                        l.update(); l.draw(self.screen,self.misa_font)
                        if l.rect.colliderect(self.ship.rect):
                            # Try to fill an unfilled slot first.
                            # If all slots already filled, award 500 bonus points instead.
                            collected = False
                            for w,pr in self.keyword_progress.items():
                                if l.char in w:
                                    for i in range(len(w)):
                                        if w[i]==l.char and not pr[i]:
                                            pr[i]=True
                                            if all(pr): self.trigger_keyword(word=w)
                                            collected=True
                                            break
                                if collected: break
                            if collected:
                                self.play_sfx('blip'); self.letters.remove(l)
                            else:
                                # Already-taken letter — bonus score
                                self.score+=500; self.play_sfx('blip'); self.letters.remove(l)
                        elif l.y>SCREEN_HEIGHT: self.letters.remove(l)

                    if self.drone_timer>now:
                        self.draw_drones()
                        pygame.draw.rect(self.screen,PURPLE,(SCREEN_WIDTH-110,SCREEN_HEIGHT-20,int(100*((self.drone_timer-now)/DRONE_DURATION_MS)),5))
                    if self.ghost_fires>0: self.draw_ghost()
                    self.ship.draw(self.screen,warp=(self.warp_timer>now),shield_active=self.shield_active,shield_hp=self.shield_hp)

                    if self.ship.is_entering:
                        elapsed_e=now-self.ship_ready_time; rem=3-(elapsed_e//1000)
                        if rem>0:
                            gr=self.menu_font.render("GET READY!",True,GREEN); self.screen.blit(gr,(SCREEN_WIDTH//2-gr.get_width()//2,SCREEN_HEIGHT//2-85))
                            cd=self.countdown_font.render(str(rem),True,YELLOW); self.screen.blit(cd,(SCREEN_WIDTH//2-cd.get_width()//2,SCREEN_HEIGHT//2-45))
                        else: self.ship.is_entering=False; self.ship.invulnerable_until=now+2000

                else:
                    for b  in self.bullets:      b.draw(self.screen)
                    for en in self.enemies:      en.draw(self.screen)
                    for bo in self.bosses:       bo.draw(self.screen)
                    for bb in self.boss_bullets: bb.draw(self.screen)
                    for p  in self.powerups:     p.draw(self.screen)
                    for l  in self.letters:      l.draw(self.screen,self.misa_font)
                    self.ship.draw(self.screen,warp=(self.warp_timer>now),strobe=self.paused,shield_active=self.shield_active,shield_hp=self.shield_hp)
                    if self.impact_flash>now:
                        fl=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT)); fl.fill(RED); fl.set_alpha(100); self.screen.blit(fl,(0,0))
                        self.hit_shockwave+=10; pygame.draw.circle(self.screen,WHITE,self.ship.rect.center,self.hit_shockwave,3)
                    if self.paused:
                        ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,155)); self.screen.blit(ov,(0,0))
                        msg=self.countdown_font.render("SHIP DESTROYED!",True,RED); self.screen.blit(msg,(SCREEN_WIDTH//2-msg.get_width()//2,SCREEN_HEIGHT//2-75))
                        rt=self.menu_font.render(f"Remaining ships:  {self.lives}",True,WHITE); self.screen.blit(rt,(SCREEN_WIDTH//2-rt.get_width()//2,SCREEN_HEIGHT//2+8))
                        prog=min(1.0,(now-self.pause_time)/1800.0); bw=240; bx=SCREEN_WIDTH//2-bw//2
                        pygame.draw.rect(self.screen,DARK_GRAY,(bx,SCREEN_HEIGHT//2+58,bw,8),border_radius=4)
                        if prog>0: pygame.draw.rect(self.screen,CYAN,(bx,SCREEN_HEIGHT//2+58,int(bw*prog),8),border_radius=4)
                        rs=self.info_font.render("RESPAWNING...",True,CYAN); self.screen.blit(rs,(SCREEN_WIDTH//2-rs.get_width()//2,SCREEN_HEIGHT//2+73))
                    if self.state==STATE_PLAYING and self.paused and now-self.pause_time>1800:
                        dur=1800; self.paused=False; self.ship_ready_time=now; self.ship.reset(True)
                        self.flare_timer+=dur; self.idle_timer+=dur; self.zapp_cooldown_timer+=dur
                        self.drone_timer+=dur; self.warp_timer+=dur; self.boss_collision_cooldown+=dur
                        for bo in self.bosses: bo.last_move_change+=dur; bo.rage_attack_timer+=dur
                        self.play_next_track(self.boss_mode, rage=self.boss_rage_active)

            elif self.state==STATE_DEATH_SEQUENCE:
                el=now-self.death_timer
                if el<1000:
                    self.ship.draw(self.screen,255 if (el//50)%2==0 else 100)
                    if self.killer_enemy: self.killer_enemy.draw(self.screen)
                    self.shake=5
                elif el<2500:
                    if el<1100:   self.play_sfx('boom_ship'); self.shake=30; self.create_explosion(self.ship.x+35,self.ship.y+40,CYAN,60,4.0); self.create_explosion(self.ship.x+35,self.ship.y+40,WHITE,40,2.0)
                    if 1500<el<1600: self.create_explosion(self.ship.x+35,self.ship.y+40,ORANGE,80,5.0); self.shake=40
                    if 2000<el<2100: self.create_explosion(self.ship.x+35,self.ship.y+40,RED,100,6.0); self.play_sfx('game_over')
                    if self.killer_enemy: self.killer_enemy.draw(self.screen)
                else:
                    fade=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); fade.fill((50,0,0,min(255,(el-2500)//4))); self.screen.blit(fade,(0,0))
                    if el>4000: self.state=STATE_CONTINUE; self.continue_timer=now; self.menu_idx=0; self.menu_count=2

            elif self.state==STATE_CONTINUE:
                rem=10-((now-self.continue_timer)//1000)
                if rem<=0: self.handle_highscore_transition()
                else: self.menu_count=2; self.draw_menu_overlay(f"Continue?  {rem}",["YES","NO"],YELLOW,small_title=True)

            elif self.state==STATE_NAME_ENTRY:
                ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,200)); self.screen.blit(ov,(0,0))
                self.screen.blit(self.info_font.render("New High Score!",True,YELLOW),(SCREEN_WIDTH//2-80,SCY-200))
                self.screen.blit(self.info_font.render(f"Score: {self.score:07}",True,WHITE),(SCREEN_WIDTH//2-80,SCY-120))
                self.screen.blit(self.info_font.render("Enter Initials (4 Chars)",True,CYAN),(SCREEN_WIDTH//2-120,SCY-50))
                for i in range(4):
                    char=ALLOWED_CHARS[self.entry_name[i]]; color=YELLOW if i==self.entry_idx else WHITE
                    img=self.info_font.render(char,True,color); self.screen.blit(img,(SCREEN_WIDTH//2-60+i*35,SCY+20))
                    if i==self.entry_idx: pygame.draw.line(self.screen,YELLOW,(SCREEN_WIDTH//2-60+i*35,SCY+45),(SCREEN_WIDTH//2-40+i*35,SCY+45),2)
                self.screen.blit(self.info_font.render("Up/Down to Cycle  -  Fire to Confirm  -  Bksp to Correct",True,DARK_GRAY),(SCREEN_WIDTH//2-220,SCY+150))

            elif self.state==STATE_VICTORY:
                el=now-self.victory_timer
                if el<1000 and (el//200)%2==0: self.screen.fill(WHITE)
                if random.random()<0.15:
                    self.create_explosion(random.randint(50,SCREEN_WIDTH-50),random.randint(50,SCREEN_HEIGHT-250),
                                          random.choice([CYAN,YELLOW,PURPLE,GREEN,ORANGE,WHITE,RED]),40,4.0); self.play_sfx('blip')
                if self.ship.y>-100:
                    self.ship.y-=8
                    if random.random()<0.5: self.particles.append(Particle(self.ship.x+35,self.ship.y+80,random.choice([CYAN,WHITE]),vy=5))
                self.ship.draw(self.screen)
                if el>3000 and self.stage in (1,2,3):
                    msg=self.countdown_font.render(f"PREPARE FOR STAGE {self.stage+1}",True,CYAN)
                    self.screen.blit(msg,(SCREEN_WIDTH//2-msg.get_width()//2,SCREEN_HEIGHT//2))
                if el>6000:
                    pygame.mixer.music.fadeout(900)
                    if self.stage in (1,2,3):
                        self.stage+=1; self.distance=0
                        self.init_stars(self.stage); self._init_nebulas(self.stage); self._init_pulsars(self.stage)
                        self.planets=[Planet(self.stage) for _ in range(3)]
                        self.reset_game(False); self.ship.reset(True); self.state=STATE_PLAYING
                    else: self.state=STATE_INTRO; self.menu_count=3; self.play_title_music()

            # =================================================================
            # HUD
            # =================================================================
            if (self.state not in (STATE_INTRO,STATE_DEATH_SEQUENCE,STATE_NAME_ENTRY,
                                   STATE_CONTINUE,STATE_VICTORY,STATE_SETTINGS,
                                   STATE_SAVE_MENU,STATE_LOAD_MENU,STATE_SAVE_NAME)
                    and self.hud_visible):
                hj=self.hud_jitter>now; hox=random.randint(-3,3) if hj else 0; hcol=RED if hj else WHITE; hal=200 if hj else 255
                ui_y=10; w_label=self.weapon.capitalize().replace("Super_laser","Super Laser")+(" [Max]" if self.weapon_tier>1 else "")
                self.screen.blit(self.hud_panel,(5,5))
                for text,col in [(f"Score: {self.display_score:07}",hcol),(f"Stage: {self.stage}",WHITE),(f"Nukes: {self.nukes}",WHITE),(f"Shields: {self.shields}",WHITE)]:
                    img=self.info_font.render(text,True,col); img.set_alpha(hal); self.screen.blit(img,(10+hox,ui_y)); ui_y+=22
                draw_arcade_symbol(self.screen,10+hox+9,ui_y+9,self.weapon,WEAPONS[self.weapon]['color'],7,False)
                wl=self.info_font.render(w_label,True,WHITE); wl.set_alpha(hal); self.screen.blit(wl,(10+hox+22,ui_y)); ui_y+=22
                dl=self.info_font.render(f"DIST  {self.distance:.2f} / {self.target_distance:.0f} Au",True,CYAN); dl.set_alpha(hal); self.screen.blit(dl,(10+hox,ui_y)); ui_y+=22
                prog=min(1.0,self.distance/self.target_distance); bw,bh=162,7
                pygame.draw.rect(self.screen,DARK_GRAY,(10+hox,ui_y,bw,bh),border_radius=3)
                if prog>0: pygame.draw.rect(self.screen,YELLOW if prog>0.8 else CYAN,(10+hox,ui_y,int(bw*prog),bh),border_radius=3)
                ui_y+=14
                for i in range(max(0,self.lives)): draw_pixel_heart(self.screen,RED,SCREEN_WIDTH-25-i*30,HUD_LIVES_Y,25)
                _PH=(48,50,60); ky=HUD_KW_Y
                for word,progress in self.keyword_progress.items():
                    full_w=sum(self.misa_font.size(c)[0] for c in word); cx2=SCREEN_WIDTH-20-full_w
                    if word=="ZAPP" and self.zapp_active:
                        elapsed=max(0,16000-(self.zapp_cooldown_timer-now)); gc=elapsed//4000
                        for i,char in enumerate(word):
                            cw=self.misa_font.size(char)[0]; self.screen.blit(self.misa_font.render(char,True,GREEN if i<gc else RED),(cx2,ky)); cx2+=cw
                        # ZAPP cooldown bar — supplementary to letter colouring
                        bar_x=SCREEN_WIDTH-20-sum(self.misa_font.size(c)[0] for c in word)
                        bar_w=sum(self.misa_font.size(c)[0] for c in word)
                        cd_prog=min(1.0,elapsed/16000.0)
                        pygame.draw.rect(self.screen,(40,40,40),(bar_x,ky+26,bar_w,3),border_radius=1)
                        if cd_prog>0: pygame.draw.rect(self.screen,GREEN,(bar_x,ky+26,int(bar_w*cd_prog),3),border_radius=1)
                    else:
                        for i,char in enumerate(word):
                            cw=self.misa_font.size(char)[0]; col=(GREEN if all(progress) else WHITE) if progress[i] else _PH
                            self.screen.blit(self.misa_font.render(char,True,col),(cx2,ky)); cx2+=cw
                    ky+=35
                if self.warp_timer>now: pygame.draw.rect(self.screen,CYAN,(SCREEN_WIDTH-110,ky+10,int(100*((self.warp_timer-now)/WARP_DURATION_MS)),4))
                if self.ghost_fires>0:
                    gi=self.info_font.render(f"Ghost Ammo: {self.ghost_fires}",True,CYAN); self.screen.blit(gi,(SCREEN_WIDTH-20-gi.get_width(),HUD_BOTTOM-16))
                # Timed bottom-centre hints — shield and ZAPP ready, never overlap.
                # Shield hint: shown for 10s after pickup, re-triggered if count changes.
                # ZAPP ready hint: shown for 10s after ZAPP letters are first completed.
                # Only one is shown at a time; ZAPP ready takes priority.
                _hint_y=HUD_BOTTOM-2
                if self.zapp_ready_timer>now:
                    pulse_a=int(160+95*abs(math.sin(now*0.004)))
                    zh=self.info_font.render("Z  -  ZAPP  READY",True,GREEN)
                    zh.set_alpha(pulse_a)
                    self.screen.blit(zh,(SCREEN_WIDTH//2-zh.get_width()//2,_hint_y))
                elif self.shield_hint_timer>now and self.shields>0 and not self.shield_active:
                    pulse_a=int(160+95*abs(math.sin(now*0.003)))
                    sh=self.info_font.render(f"C  -  SHIELD  x{self.shields}",True,CYAN)
                    sh.set_alpha(pulse_a)
                    self.screen.blit(sh,(SCREEN_WIDTH//2-sh.get_width()//2,_hint_y))

            # =================================================================
            # OVERLAY MENUS
            # =================================================================
            if self.state==STATE_INTRO:
                opts=(["START MISSION","LOAD GAME","SETTINGS","QUIT GAME"] if self._save_exists()
                      else ["START MISSION","SETTINGS","QUIT GAME"])
                self.menu_count=len(opts); self.draw_menu_overlay("ULTRA SPACE ARCADE",opts,BLUE)
            elif self.state==STATE_PAUSED:    self.draw_menu_overlay("MISSION PAUSED",["RESUME","SAVE GAME","SETTINGS","ABANDON MISSION"],CYAN)
            elif self.state==STATE_GAME_OVER: self.draw_menu_overlay("MISSION FAILED",["TRY AGAIN","QUIT TO MENU"],RED)
            elif self.state==STATE_CLEARED:   self.draw_menu_overlay("STAGE CLEARED",["NEXT MISSION","QUIT TO MENU"],GREEN)
            elif self.state==STATE_SETTINGS:  self._draw_settings_menu()
            elif self.state==STATE_SAVE_MENU: self._draw_save_menu()
            elif self.state==STATE_LOAD_MENU: self._draw_load_menu()
            elif self.state==STATE_SAVE_NAME: self._draw_save_name_entry()

            # Hidden hotkey panel (PAUSED + H)
            if self.state==STATE_PAUSED and self.show_hotkeys:
                pw,ph=520,390; ppx,ppy=SCREEN_WIDTH//2-pw//2,SCREEN_HEIGHT//2-ph//2
                self.screen.blit(_glass_surface(pw,ph),(ppx,ppy))
                tt=self.menu_font.render("HOTKEY  REFERENCE",True,CYAN); self.screen.blit(tt,(SCREEN_WIDTH//2-tt.get_width()//2,ppy+12))
                pygame.draw.line(self.screen,(50,80,160),(ppx+16,ppy+38),(ppx+pw-16,ppy+38),1)
                col1=[("MOVEMENT",""),("W/↑  S/↓  A/←  D/→","Move ship"),("",""),
                       ("COMBAT",""),("SPACE","Fire weapon"),("X","Launch nuke"),("C","Activate shield"),
                       ("Z","Fire ZAPP beam"),("`","Instant side drones"),("",""),
                       ("SYSTEM",""),("ESC","Pause / Resume / Back"),("H  (gameplay)","Toggle HUD"),
                       ("H  (paused)","Toggle this panel"),("F12","Screenshot")]
                col2=[("DEV  (SHIFT required)",""),("SHIFT+F1","Refill lives to 6"),("SHIFT+F2","Add 3 nukes"),
                       ("SHIFT+F3","Jump to 9.0 AU"),("SHIFT+F4","Skip to next stage"),("SHIFT+F5","Trigger boss now"),
                       ("SHIFT+F6","Max all weapons"),("SHIFT+F7","Force Super Laser"),("SHIFT+F8","Cycle weapon"),
                       ("",""),("TITLE SCREEN",""),("M","Toggle title music"),("",""),("SETTINGS",""),
                       ("TRAJECTORY","Lean-to-fire on / off")]
                lh=22; cy0=ppy+46; cx1=ppx+14; cx2=ppx+pw//2+8; HDR=(100,160,255); DIM=(130,130,150)
                for i,(key,desc) in enumerate(col1):
                    if not key and not desc: continue
                    y=cy0+i*lh
                    if not desc: self.screen.blit(self.info_font.render(key,True,HDR),(cx1,y))
                    else:
                        ki=self.info_font.render(key,True,YELLOW); self.screen.blit(ki,(cx1,y))
                        self.screen.blit(self.info_font.render(desc,True,DIM),(cx1+ki.get_width()+6,y))
                for i,(key,desc) in enumerate(col2):
                    if not key and not desc: continue
                    y=cy0+i*lh
                    if not desc: self.screen.blit(self.info_font.render(key,True,HDR),(cx2,y))
                    else:
                        ki=self.info_font.render(key,True,YELLOW); self.screen.blit(ki,(cx2,y))
                        self.screen.blit(self.info_font.render(desc,True,DIM),(cx2+ki.get_width()+6,y))
                hint=self.info_font.render("H  close",True,(55,65,90))
                self.screen.blit(hint,(SCREEN_WIDTH//2-hint.get_width()//2,ppy+ph-20))

            self.screen.blit(self.vignette,(0,0))

            if self.save_flash>now:
                fr=(self.save_flash-now)/1200.0; sv=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
                sv.fill((0,30,60,int(80*fr))); self.screen.blit(sv,(0,0))
                si=self.info_font.render("Game Saved!",True,CYAN); self.screen.blit(si,(SCREEN_WIDTH//2-si.get_width()//2,HUD_BOTTOM-22))
            if self.screenshot_flash>now:
                fr=(self.screenshot_flash-now)/900.0; fl=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
                fl.fill((255,255,255,int(210*fr))); self.screen.blit(fl,(0,0))
                si=self.info_font.render("Screenshot saved!",True,YELLOW); self.screen.blit(si,(SCREEN_WIDTH//2-si.get_width()//2,HUD_BOTTOM-22))

            # -----------------------------------------------------------------
            # RAGE MODE FLASH
            # -----------------------------------------------------------------
            if self.rage_flash_timer>now:
                fr=(self.rage_flash_timer-now)/2500.0
                rf=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
                rf.fill((180,0,0,int(120*fr))); self.screen.blit(rf,(0,0))
                pulse=abs(math.sin((2500-(self.rage_flash_timer-now))*0.006))
                ra=int(200+55*pulse)
                rm=self.countdown_font.render("RAGE MODE",True,(ra,0,0))
                rs=pygame.Surface((rm.get_width()+20,rm.get_height()+10),pygame.SRCALPHA)
                rs.fill((0,0,0,int(160*fr)))
                self.screen.blit(rs,(SCREEN_WIDTH//2-rs.get_width()//2,SCREEN_HEIGHT//2-rs.get_height()//2))
                rm.set_alpha(int(255*fr))
                self.screen.blit(rm,(SCREEN_WIDTH//2-rm.get_width()//2,SCREEN_HEIGHT//2-rm.get_height()//2+5))

            # -----------------------------------------------------------------
            # STAGE BRIEFING OVERLAY
            # -----------------------------------------------------------------
            if self.stage_briefing_timer>now and self.state==STATE_PLAYING:
                _STAGE_NAMES={1:"OUTER BELT",2:"DEEP SPACE",3:"FINAL APPROACH",4:"VOID RIFT"}
                _BRIEFINGS={
                    1:"Patrol the outer belt. Eliminate all hostiles.",
                    2:"Deep space sector. Warships detected. Stay sharp.",
                    3:"Final approach. The twin planets must be destroyed.",
                    4:"Reality fractures here. Nothing is what it seems.",
                }
                fr=min(1.0,(self.stage_briefing_timer-now)/3500.0)
                alpha=int(255*min(fr*4,1.0)*min((1.0-fr)*4,1.0))
                alpha=max(0,min(255,alpha))
                _BY=STAGE_BRIEF_Y
                sb=pygame.Surface((SCREEN_WIDTH,64),pygame.SRCALPHA)
                sb.fill((0,0,0,int(180*(alpha/255))))
                self.screen.blit(sb,(0,_BY))
                stage_label=f"STAGE  {self.stage}  —  {_STAGE_NAMES.get(self.stage,'')}"
                stg=self.menu_font.render(stage_label,True,CYAN)
                stg.set_alpha(alpha)
                self.screen.blit(stg,(SCREEN_WIDTH//2-stg.get_width()//2,_BY+6))
                brief=self.info_font.render(_BRIEFINGS.get(self.stage,""),True,WHITE)
                brief.set_alpha(alpha)
                self.screen.blit(brief,(SCREEN_WIDTH//2-brief.get_width()//2,_BY+36))

            pygame.display.flip()
            if self.pending_screenshot: self.pending_screenshot=False; self.take_screenshot()

    # =========================================================================
    # HELPERS
    # =========================================================================
    def draw_drones(self):
        draw_arcade_symbol(self.screen,int(self.ship.x-40), int(self.ship.y+20),'drone',PURPLE,12)
        draw_arcade_symbol(self.screen,int(self.ship.x+110),int(self.ship.y+20),'drone',PURPLE,12)

    def draw_ghost(self):
        gx=SCREEN_WIDTH-self.ship.x-self.ship.width; ay_s=SCREEN_HEIGHT//2; ay_e=SCREEN_HEIGHT-self.ship.height
        gy=ay_s+(ay_e-self.ship.y); a=int(120+100*math.sin(pygame.time.get_ticks()*0.01))
        draw_pixel_heart(self.screen,RED,       gx+12,              gy+self.ship.height-20,35,True, a//2)
        draw_pixel_heart(self.screen,RED,       gx+self.ship.width-12,gy+self.ship.height-20,35,True,a//2)
        draw_pixel_heart(self.screen,GHOST_COLOR,gx+35,gy+40,75,True,a)
        draw_pixel_heart(self.screen,CYAN,       gx+35,gy+28,18,False,a)

    def ghost_fire(self):
        gx=SCREEN_WIDTH-self.ship.x-self.ship.width; ay_s=SCREEN_HEIGHT//2; ay_e=SCREEN_HEIGHT-self.ship.height
        gy=ay_s+(ay_e-self.ship.y); cx,y=gx+self.ship.width//2,gy
        if   self.weapon=='normal':  self.bullets.append(Bullet(cx,y,'ghost_normal',color=GHOST_COLOR))
        elif self.weapon=='dual':    self.bullets.extend([Bullet(cx-18,y-10,'ghost_dual',color=GHOST_COLOR),Bullet(cx+18,y-10,'ghost_dual',color=GHOST_COLOR)])
        elif self.weapon=='triple':
            for a in (0,-0.25,0.25): self.bullets.append(Bullet(cx,y,'ghost_triple',a,color=GHOST_COLOR))
        elif self.weapon in ('laser','super_laser'): self.bullets.append(Bullet(cx,y,'ghost_laser',color=GHOST_COLOR))
        elif self.weapon=='blast':
            for ang in (0,2.094,4.188): self.bullets.append(Bullet(cx,y,'ghost_blast',orbit_angle=ang,color=GHOST_COLOR))

    def fire(self):
        now=pygame.time.get_ticks()
        rate=WEAPONS[self.weapon]['rate']
        if self.weapon_tier>1 and self.weapon not in ('laser','super_laser'): rate//=2
        if now-self.last_fire<rate: return
        if len(self.bullets)>=80: return
        self.last_fire=now; self.play_sfx(WEAPONS[self.weapon]['sound'])
        cx,y=self.ship.x+self.ship.width//2,self.ship.y
        lr=math.radians(self.ship.lean*3.4) if self.trajectory_enabled else 0.0
        if   self.weapon=='normal':  self.bullets.append(Bullet(cx,y,'normal',lr))
        elif self.weapon=='dual':    self.bullets.extend([Bullet(cx-18,y+10,'dual',lr),Bullet(cx+18,y+10,'dual',lr)])
        elif self.weapon=='triple':
            for a in (lr,lr-0.25,lr+0.25): self.bullets.append(Bullet(cx,y,'triple',a))
        elif self.weapon=='laser':
            if self.weapon_tier>1:
                off=-12 if self.super_laser_toggle else 12
                self.bullets.append(Bullet(cx+off,y,'super_laser',lr)); self.super_laser_toggle=not self.super_laser_toggle
            else: self.bullets.append(Bullet(cx,y,'laser',lr))
        elif self.weapon=='blast':
            for ang in (0,2.094,4.188): self.bullets.append(Bullet(cx,y,'blast',orbit_angle=ang))
            self.shake=3
        elif self.weapon=='super_laser':
            off=-15 if self.super_laser_toggle else 15
            self.bullets.append(Bullet(cx+off,y,'super_laser',lr)); self.super_laser_toggle=not self.super_laser_toggle
        if self.drone_timer>now:
            self.bullets.append(Bullet(self.ship.x-40, self.ship.y+20,'drone_laser',angle= math.pi*0.1,color=PURPLE))
            self.bullets.append(Bullet(self.ship.x+110,self.ship.y+20,'drone_laser',angle=-math.pi*0.1,color=PURPLE))
        if self.ghost_fires>0: self.ghost_fire(); self.ghost_fires-=1


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__=="__main__":
    try: Game().run()
    except Exception:
        import traceback; traceback.print_exc(); input("Press Enter to exit...")