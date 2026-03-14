import pygame
import random
import math
import os
import json
import sys

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHIP_SPEED = 6
NUKE_COOLDOWN = 3000
AU_TIME_MS = 30000
IDLE_LIMIT_MS = 5000 
DRONE_DURATION_MS = 15000
GHOST_MAX_FIRES = 150
WARP_DURATION_MS = 15000
BOSS_TRIGGER_AU = 9.9
BOSS_RADIUS = 68
HIGHSCORE_FILE = "highscore.json"

# Game States
STATE_INTRO = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAME_OVER = 3
STATE_CLEARED = 4
STATE_DEATH_SEQUENCE = 5
STATE_NAME_ENTRY = 6
STATE_CONTINUE = 7
STATE_VICTORY = 8

# Colors
BLACK = (5, 5, 10)
WHITE = (240, 240, 255)
RED = (255, 45, 80)
BLUE = (0, 150, 255)
CYAN = (0, 255, 230)
YELLOW = (255, 230, 0)
ORANGE = (255, 130, 0)
GREEN = (50, 255, 100)
PURPLE = (180, 50, 255)
DARK_GRAY = (30, 30, 40)
BROWN = (100, 50, 20)
GHOST_COLOR = (150, 220, 255)
MAROON = (128, 0, 0)

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
# HELPER FUNCTIONS
# =============================================================================
def draw_arcade_symbol(screen, x, y, s_type, color, size=20, glow=True, alpha=255):
    if glow:
        glow_color = (color[0]//3, color[1]//3, color[2]//3)
        draw_arcade_symbol(screen, x, y, s_type, glow_color, size + 4, False, alpha)
    
    surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
    lx, ly = size, size
    if s_type == 'normal':
        pygame.draw.lines(surf, (*color, alpha), False, [(lx-size//2, ly+size//2), (lx, ly-size//2), (lx+size//2, ly+size//2)], 3)
    elif s_type == 'dual':
        pygame.draw.lines(surf, (*color, alpha), False, [(lx-size//2-4, ly+size//2), (lx-4, ly-size//2), (lx+size//2-4, ly+size//2)], 2)
        pygame.draw.lines(surf, (*color, alpha), False, [(lx-size//2+4, ly+size//2), (lx+4, ly-size//2), (lx+size//2+4, ly+size//2)], 2)
    elif s_type == 'triple':
        pygame.draw.lines(surf, (*color, alpha), False, [(lx-size, ly+size//2), (lx-size//2, ly-size//2), (lx, ly+size//2)], 2)
        pygame.draw.lines(surf, (*color, alpha), False, [(lx-size//2, ly+size//2), (lx, ly-size), (lx+size//2, ly+size//2)], 2)
        pygame.draw.lines(surf, (*color, alpha), False, [(lx, ly+size//2), (lx+size//2, ly-size//2), (lx+size, ly+size//2)], 2)
    elif s_type == 'laser' or s_type == 'ghost_laser' or s_type == 'drone_laser' or s_type == 'super_laser':
        pygame.draw.rect(surf, (*color, alpha), (lx-2, ly-size, 4, size*2))
        pygame.draw.line(surf, (*WHITE, alpha), (lx-size//2, ly-size//2), (lx+size//2, ly-size//2), 2)
    elif s_type == 'blast' or s_type == 'ghost_blast':
        pygame.draw.circle(surf, (*color, alpha), (lx, ly), size//2, 3)
        for i in range(4):
            ang = i * (math.pi/2)
            pygame.draw.line(surf, (*WHITE, alpha), (lx, ly), (lx+math.cos(ang)*size, ly+math.sin(ang)*size), 2)
    elif s_type == 'nuke':
        pygame.draw.polygon(surf, (*color, alpha), [(lx, ly-size), (lx-size, ly+size//2), (lx+size, ly+size//2)], 3)
        pygame.draw.circle(surf, (*color, alpha), (lx, ly-2), size//4)
    elif s_type == 'drone':
        pygame.draw.polygon(surf, (*PURPLE, alpha), [(lx-size//2, ly+size//2), (lx, ly-size//2), (lx+size//2, ly+size//2)], 2)
    elif s_type == 'ghost':
        pygame.draw.polygon(surf, (*CYAN, alpha), [(lx-size//2, ly+size//2), (lx, ly-size//2), (lx+size//2, ly+size//2)], 3)
        pygame.draw.circle(surf, (*WHITE, alpha), (lx, ly), size//4)
    screen.blit(surf, (x-size, y-size))

def draw_pixel_heart(screen, color, x, y, size, reversed_y=False, alpha=255):
    ps = max(1, size // 7)
    pattern = [[0, 1, 1, 0, 1, 1, 0], [1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1], [0, 1, 1, 1, 1, 1, 0], [0, 0, 1, 1, 1, 0, 0], [0, 0, 0, 1, 0, 0, 0]]
    if reversed_y: pattern = pattern[::-1]
    surf = pygame.Surface((len(pattern[0])*ps, len(pattern)*ps), pygame.SRCALPHA)
    for r, row in enumerate(pattern):
        for c, val in enumerate(row):
            if val:
                pygame.draw.rect(surf, (*color, alpha), (c * ps, r * ps, ps, ps))
                pygame.draw.rect(surf, (0,0,0, alpha), (c * ps, r * ps, ps, ps), 1)
    screen.blit(surf, (x - surf.get_width()//2, y - surf.get_height()//2))

# =============================================================================
# ENTITY CLASSES
# =============================================================================
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, speed=1.0):
        self.x, self.y, self.color = x, y, color
        self.vx = (vx if vx is not None else random.uniform(-3, 3)) * speed
        self.vy = (vy if vy is not None else random.uniform(-3, 3)) * speed
        self.life = 255
    def update(self):
        self.x += self.vx; self.y += self.vy; self.life -= 8
    def draw(self, screen):
        if self.life > 0:
            s = pygame.Surface((3, 3), pygame.SRCALPHA)
            s.fill((*self.color, self.life))
            screen.blit(s, (self.x, self.y))

class Bullet:
    def __init__(self, x, y, w_key, angle=0, orbit_angle=0, color=None):
        self.x, self.y, self.center_x, self.center_y = x, y, x, y
        self.config = WEAPONS[w_key] if w_key in WEAPONS else {'color': color or WHITE, 'speed': 18}
        self.w_key, self.angle, self.orbit_angle = w_key, angle, orbit_angle
        self.radius = 4 if 'blast' not in w_key else 10; self.rect = pygame.Rect(x-self.radius, y-self.radius, self.radius*2, self.radius*2)
    def update(self, speed_mult=1.0):
        if 'blast' in self.w_key:
            self.center_y -= self.config['speed'] * speed_mult; self.orbit_angle += 0.25; self.x = self.center_x + math.cos(self.orbit_angle) * 30; self.y = self.center_y + math.sin(self.orbit_angle) * 30
        else:
            self.x += math.sin(self.angle) * self.config['speed'] * speed_mult; self.y -= math.cos(self.angle) * self.config['speed'] * speed_mult
        self.rect.center = (int(self.x), int(self.y))
    def draw(self, screen):
        color = self.config['color']
        if 'laser' in self.w_key or 'super_laser' in self.w_key or 'drone_laser' in self.w_key:
            surf = pygame.Surface((4, 30), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, 4, 30))
            pygame.draw.rect(surf, WHITE, (1, 5, 2, 20))
            rot_surf = pygame.transform.rotate(surf, math.degrees(self.angle))
            screen.blit(rot_surf, (self.x - rot_surf.get_width()//2, self.y - rot_surf.get_height()//2))
        elif 'blast' in self.w_key:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius); pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius-4)
        else:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)

class Mortar:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.rect = pygame.Rect(x-10, y-10, 20, 20)
        self.detonated = False
    def update(self):
        self.x += self.vx; self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        if self.y <= 120: self.detonated = True

class Spaceship:
    def __init__(self):
        self.width, self.height = 70, 80; self.invulnerable_until = 0; self.reset(entering=True)
    def reset(self, entering=False):
        self.target_x, self.target_y = SCREEN_WIDTH // 2 - self.width // 2, SCREEN_HEIGHT - self.height - 30
        self.x, self.y = self.target_x, SCREEN_HEIGHT + 100 if entering else self.target_y
        self.is_entering = entering; self.rect = pygame.Rect(self.x, self.y, self.width, self.height); self.flicker = 0
        if entering: self.invulnerable_until = pygame.time.get_ticks() + 10000 
    def is_invulnerable(self, warp=False):
        return self.is_entering or warp or pygame.time.get_ticks() < self.invulnerable_until
    def move(self, keys):
        if self.is_entering:
            if self.y > self.target_y: self.y -= 4
            else: self.y = self.target_y
        else:
            if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.y > SCREEN_HEIGHT//2: self.y -= SHIP_SPEED
            if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and self.y < SCREEN_HEIGHT - self.height: self.y += SHIP_SPEED
            if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and self.x > 0: self.x -= SHIP_SPEED
            if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and self.x < SCREEN_WIDTH - self.width: self.x += SHIP_SPEED
        self.rect.topleft = (self.x, self.y)
    def draw(self, screen, alpha=255, warp=False, strobe=False):
        self.flicker = (self.flicker + 1) % 10
        if strobe:
            if (pygame.time.get_ticks() // 40) % 2 == 0: return
        elif self.is_invulnerable(warp) and self.flicker < 5 and not warp: return 
        cx, cy = self.x + self.width//2, self.y + self.height//2
        if warp:
            for i in range(3): pygame.draw.circle(screen, random.choice([CYAN, BLUE, WHITE]), (cx, cy), 50 + i*5, 2)
        if alpha == 255: pygame.draw.polygon(screen, ORANGE, [(cx-15, self.y+self.height-10), (cx+15, self.y+self.height-10), (cx, self.y+self.height+random.randint(10, 30))])
        draw_pixel_heart(screen, RED, self.x+12, self.y+self.height-20, 35, True, alpha); draw_pixel_heart(screen, RED, self.x+self.width-12, self.y+self.height-20, 35, True, alpha)
        draw_pixel_heart(screen, BLUE, cx, cy, 75, True, alpha); draw_pixel_heart(screen, CYAN, cx, cy-12, 18, False, alpha)

class Enemy:
    def __init__(self, is_tank=False, is_unbreakable=False, is_comet=False, target_pos=None):
        self.is_tank, self.is_unbreakable, self.is_comet = is_tank, is_unbreakable, is_comet
        self.hp = 6 if is_tank else (10 if is_comet else 1); self.max_hp = self.hp
        if is_unbreakable: self.hp = 999
        self.radius = 12 if is_comet else (random.randint(45, 60) if (is_tank or is_unbreakable) else random.randint(18, 28))
        if is_comet:
            self.x, self.y = random.randint(0, SCREEN_WIDTH), -50
            angle = math.atan2(target_pos[1] - self.y, target_pos[0] - self.x)
            self.vx, self.vy = math.cos(angle) * 8, math.sin(angle) * 8; self.color = WHITE
        else:
            self.x, self.y = random.randint(self.radius, SCREEN_WIDTH - self.radius), -self.radius * 2
            self.vx, self.vy = 0, random.uniform(1.0, 1.8) if is_unbreakable else (random.uniform(1.2, 2.2) if is_tank else random.uniform(3.5, 7))
            self.color = BROWN if is_unbreakable else ((50, 50, 70) if is_tank else (110, 110, 120))
        self.offsets = [self.radius * (0.8 + 0.4 * random.random()) for _ in range(12)]
        self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius, self.radius*2, self.radius*2); self.pulse = 0
    def hit(self):
        if self.is_unbreakable: return False
        self.hp -= 1
        if self.is_tank or self.is_comet:
            self.radius = max(10, int(self.radius * 0.85)); self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius, self.radius*2, self.radius*2); self.offsets = [self.radius * (0.8 + 0.4 * random.random()) for _ in range(12)]
        return self.hp <= 0
    def update(self, particles=None, speed_mult=1.0):
        self.x += self.vx * speed_mult; self.y += self.vy * speed_mult; self.rect.center = (int(self.x), int(self.y))
        if self.is_unbreakable: self.pulse = (self.pulse + 0.1) % (math.pi * 2)
        if self.is_comet and particles is not None:
            for _ in range(3): particles.append(Particle(self.x, self.y, random.choice([ORANGE, YELLOW, RED]), -self.vx*0.5 + random.uniform(-1,1), -self.vy*0.5 + random.uniform(-1,1)))
    def draw(self, screen):
        pts = [(self.x + self.offsets[i]*math.cos(i*math.pi/6), self.y + self.offsets[i]*math.sin(i*math.pi/6)) for i in range(12)]
        pygame.draw.polygon(screen, self.color, pts)
        if self.is_unbreakable: pygame.draw.polygon(screen, (int(127 + 127 * math.sin(self.pulse)), 0, 0), pts, 3)
        elif self.is_comet: pygame.draw.polygon(screen, ORANGE, pts, 2); pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius // 2)
        else: pygame.draw.polygon(screen, WHITE if self.is_tank else DARK_GRAY, pts, 1)

class BossPlanet:
    def __init__(self, x, side_id):
        self.radius = BOSS_RADIUS; self.x, self.y = x, 100; self.target_y = 120; self.hp = 200; self.max_hp = 200
        self.side_id = side_id; self.alpha = 0
        self.vx = random.uniform(1.5, 3.0) * (1 if side_id == 0 else -1)
        self.vy = random.uniform(-1.0, 1.0); self.last_move_change = 0
        self.offsets = [self.radius * (0.9 + 0.2 * random.random()) for _ in range(24)]
        self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius, self.radius*2, self.radius*2)
        self.is_rage = False; self.invulnerable = False; self.shake_timer = 0
        self.is_dying = False; self.death_timer = 0; self.rage_attack_timer = 0
    def update(self):
        now = pygame.time.get_ticks()
        if self.is_dying: return None
        if self.alpha < 255: self.alpha += 2
        
        move_freq = 2000 if self.is_rage else 4000
        if now - self.last_move_change > move_freq:
            speed_range = (3.5, 5.5) if self.is_rage else (1.5, 3.0)
            self.vx = random.uniform(*speed_range) * (1 if self.vx > 0 else -1)
            self.vy = random.uniform(-1.5, 1.5); self.last_move_change = now
        self.x += self.vx; self.y += self.vy
        if self.x < self.radius or self.x > SCREEN_WIDTH - self.radius: self.vx *= -1
        if self.y < 50 or self.y > 350: self.vy *= -1
        self.rect.center = (int(self.x), int(self.y))
        if self.shake_timer > 0: self.shake_timer -= 1
        if self.is_rage and now > self.rage_attack_timer:
            self.rage_attack_timer = now + 4000; return "shockwave"
        return None
    def draw(self, screen, font):
        now = pygame.time.get_ticks()
        if self.is_dying:
            if (now // 50) % 2 == 0: return
            alpha = max(0, 255 - (now - self.death_timer) // 4)
        else: alpha = max(0, min(255, int(self.alpha)))
        sx, sy = (self.x + random.randint(-2,2) if self.shake_timer > 0 else self.x, self.y + random.randint(-2,2) if self.shake_timer > 0 else self.y)
        pts = [(sx + self.offsets[i]*math.cos(i*math.pi/12), sy + self.offsets[i]*math.sin(i*math.pi/12)) for i in range(24)]
        hp_val = int(self.hp)
        if self.is_rage:
            r = max(60, min(128, hp_val + 40)); color = (r, 0, 0); eye_color = PURPLE
        else: color = (max(0, min(255, hp_val + 50)), 50, 50); eye_color = RED
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*color, alpha), pts); pygame.draw.polygon(s, (255, 255, 255, alpha), pts, 2)
        pygame.draw.rect(s, (*eye_color, alpha), (int(sx - 25), int(sy - 15), 15, 8))
        pygame.draw.rect(s, (*eye_color, alpha), (int(sx + 10), int(sy - 15), 15, 8))
        screen.blit(s, (0,0))
        if not self.is_dying:
            hb_w = 100; pygame.draw.rect(screen, DARK_GRAY, (int(self.x - hb_w//2), int(self.y - self.radius - 20), hb_w, 8))
            pygame.draw.rect(screen, RED if not self.is_rage else YELLOW, (int(self.x - hb_w//2), int(self.y - self.radius - 20), int(hb_w * (self.hp/self.max_hp)), 8))

class BossProjectile:
    def __init__(self, x, y, vx, vy, size=20, color=WHITE):
        self.x, self.y, self.vx, self.vy, self.size, self.color = x, y, vx, vy, size, color
        self.rect = pygame.Rect(x-size//2, y-size//2, size, size)
    def update(self):
        self.x += self.vx; self.y += self.vy; self.rect.center = (int(self.x), int(self.y))
    def draw(self, screen): 
        pygame.draw.polygon(screen, self.color, [(self.x, self.y+self.size), (self.x-self.size//2, self.y-self.size//2), (self.x+self.size//2, self.y-self.size//2)])

class LetterItem:
    def __init__(self, x, y, char):
        self.x, self.y, self.char = x, y, char; self.rect = pygame.Rect(x-15, y-15, 30, 30); self.pulse = 0
    def update(self): self.y += 2; self.pulse = (self.pulse + 0.1) % (math.pi * 2); self.rect.center = (int(self.x), int(self.y))
    def draw(self, screen, font):
        val = int(150 + 100 * math.sin(self.pulse)); color = (val, val, 255); img = font.render(self.char, True, color)
        glow_size = max(img.get_width(), img.get_height()) + 15; s = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA); pygame.draw.circle(s, (0, 100, 255, 60), (glow_size//2, glow_size//2), glow_size//2)
        screen.blit(s, (self.x - glow_size//2, self.y - glow_size//2)); screen.blit(img, (self.x - img.get_width()//2, self.y - img.get_height()//2))

class PowerUp:
    def __init__(self, x, y, p_type):
        self.x, self.y, self.p_type = x, y, p_type; self.rect = pygame.Rect(x-20, y-20, 40, 40); self.start_x, self.angle = x, 0
        self.color = PURPLE if p_type in ['drone', 'ghost'] else (GREEN if p_type == 'nuke' else WEAPONS[p_type]['color'])
    def update(self):
        self.angle += 0.04; self.x = self.start_x + math.sin(self.angle) * 60; self.y += 2.5; self.rect.center = (int(self.x), int(self.y))
    def draw(self, screen): draw_arcade_symbol(screen, int(self.x), int(self.y), self.p_type, self.color, 18)

class Planet:
    def __init__(self): self.reset()
    def reset(self):
        self.x, self.y = random.randint(0, SCREEN_WIDTH), random.randint(-1000, -100); self.radius = random.randint(40, 120); base = random.randint(20, 50); self.color = (base, base, base + 20); self.speed = random.uniform(0.3, 0.8)
        self.craters = [(random.randint(-self.radius//2, self.radius//2), random.randint(-self.radius//2, self.radius//2), random.randint(5, 15)) for _ in range(5)]; self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
    def update(self, speed_mult=1.0): self.y += self.speed * speed_mult; self.rect.center = (int(self.x), int(self.y)); (self.y > SCREEN_HEIGHT + self.radius and self.reset())
    def draw(self, screen, offset=(0,0)):
        pygame.draw.circle(screen, self.color, (int(self.x + offset[0]), int(self.y + offset[1])), self.radius)
        for cx, cy, cr in self.craters: pygame.draw.circle(screen, (max(0, self.color[0]-10), max(0, self.color[1]-10), max(0, self.color[2]-10)), (int(self.x + cx + offset[0]), int(self.y + cy + offset[1])), cr)

class Game:
    def __init__(self):
        pygame.init(); pygame.mixer.init(); self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)); pygame.display.set_caption("ULTRA SPACE ARCADE v0.6")
        self.clock = pygame.time.Clock()
        self.base_path = os.path.dirname(os.path.abspath(__file__)); self.highscore_path = os.path.join(self.base_path, "highscore.json")
        res_path = os.path.join(self.base_path, "Resourses")
        def load_custom_font(name, size):
            p = os.path.join(res_path, name)
            return pygame.font.Font(p, size) if os.path.exists(p) else pygame.font.SysFont("monospace", size, bold=True)
        self.title_font = load_custom_font("Masterpiece.ttf", 60); self.misa_font = load_custom_font("13_Misa.TTF", 22); self.menu_font = load_custom_font("Orbitron-VariableFont_wght.ttf", 20); self.countdown_font = load_custom_font("Orbitron-VariableFont_wght.ttf", 48); self.info_font = load_custom_font("Epyval.ttf", 16)
        self.stars = [[random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.uniform(1, 5)] for _ in range(100)]; self.planets = [Planet() for _ in range(3)]; self.particles, self.shake, self.last_fire = [], 0, 0
        self.load_audio(); self.load_highscores(); self.state = STATE_INTRO; self.menu_idx = 0; self.menu_count = 2; self.reset_game(True)
    def load_audio(self):
        self.music_path, self.effects_path = os.path.join(self.base_path, "Music"), os.path.join(self.base_path, "Effects")
        self.music_tracks = [os.path.join(self.music_path, f) for f in os.listdir(self.music_path) if f.endswith(('.mp3', '.wav'))] if os.path.exists(self.music_path) else []
        self.boss_music_path = os.path.join(self.music_path, "Boss"); self.boss_tracks = [os.path.join(self.boss_music_path, f) for f in os.listdir(self.boss_music_path) if f.endswith('.mp3')] if os.path.exists(self.boss_music_path) else []
        random.shuffle(self.music_tracks); self.current_track_idx, self.music_stopped = 0, False; pygame.mixer.music.set_volume(0.4)
        self.sounds = {}
        if os.path.exists(self.effects_path):
            mappings = {'shoot_normal': 'Shoot1.wav', 'shoot_dual': 'Shoot2.wav', 'shoot_triple': 'Shoot3.wav', 'shoot_laser': 'Shoot10.wav', 'shoot_blast': 'Shoot20.wav', 'boom_normal': 'Boom1.wav', 'boom_tank': 'Boom10.wav', 'boom_nuke': 'Boom15.wav', 'boom_ship': 'Boom18.wav', 'hit_normal': 'Hit1.wav', 'hit_tank': 'Hit11.wav', 'powerup': 'PowerUp.wav', 'game_over': 'Random3.wav', 'warning': 'Mutant.wav', 'blip': 'Blip.wav', 'warp': 'Random1.wav', 'zap': 'Shoot25.wav', 'boss_impact': 'Boom12.wav'}
            for k, v in mappings.items():
                p = os.path.join(self.effects_path, v)
                if os.path.exists(p): self.sounds[k] = pygame.mixer.Sound(p); self.sounds[k].set_volume(0.55)
    def load_highscores(self):
        if os.path.exists(self.highscore_path):
            try:
                with open(self.highscore_path, 'r') as f: self.highscores = json.load(f)
            except: self.highscores = []
        else: self.highscores = []
        self.highscores = sorted(self.highscores, key=lambda x: x['score'], reverse=True)[:5]
    def save_highscores(self):
        try:
            self.highscores = sorted(self.highscores, key=lambda x: x['score'], reverse=True)[:5]
            with open(self.highscore_path, 'w') as f: json.dump(self.highscores, f)
        except: pass
    def play_sfx(self, key): (key in self.sounds and self.sounds[key].play())
    def play_next_track(self, boss=False):
        tracks = self.boss_tracks if boss else self.music_tracks
        if tracks: pygame.mixer.music.load(random.choice(tracks) if boss else tracks[self.current_track_idx]); pygame.mixer.music.play(); self.current_track_idx = (self.current_track_idx + 1) % len(tracks)
    def reset_game(self, full=False):
        self.bullets, self.enemies, self.powerups, self.letters, self.boss_bullets, self.mortars = [], [], [], [], [], []; self.paused = self.stage_cleared = False; self.pause_time = 0; self.ship_ready_time = pygame.time.get_ticks(); self.music_stopped = False; self.idle_timer = pygame.time.get_ticks(); self.last_ship_pos = (0,0); self.unbreakable_hits = 0; self.drone_timer = 0; self.ghost_fires = 0; self.death_timer = 0; self.killer_enemy = None; self.zapp_y = None; self.warp_timer = 0; self.keyword_progress = {"LIFE": [False]*4, "ZAPP": [False]*4, "BOOST": [False]*5}; self.bosses = []; self.boss_mode = False; self.boss_intro_done = False; self.flare_timer = 0; self.victory_timer = 0; self.boss_hits_received = 0; self.zapp_active = False; self.zapp_cooldown_timer = 0; self.super_laser_toggle = False; self.weapon_tier = 1; self.impact_flash = 0; self.hit_shockwave = 0
        self.entry_name = [0, 0, 0, 0]; self.entry_idx = 0; self.continue_timer = 0
        if full: self.ship = Spaceship(); self.score, self.lives, self.nukes, self.weapon, self.stage, self.frames, self.distance, self.target_distance = 0, 3, 1, 'normal', 1, 0, 0.0, 10.0
        if self.state == STATE_PLAYING: self.play_next_track()
    def create_explosion(self, x, y, color, count=15, speed=1.0):
        for _ in range(count): self.particles.append(Particle(x, y, color, speed=speed))
    def draw_menu_overlay(self, title, options, color, small_title=False):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); ov.fill((0, 0, 0, 180)); self.screen.blit(ov, (0,0))
        t_img = self.title_font.render(title, True, color); self.screen.blit(t_img, (SCREEN_WIDTH//2 - t_img.get_width()//2, 80 if not small_title else 150))
        for i, opt in enumerate(options):
            c = YELLOW if i == self.menu_idx else WHITE; f = self.info_font if (self.state == STATE_CONTINUE or "YES" in opt) else self.menu_font; img = f.render("> "+opt+" <" if i == self.menu_idx else opt, True, c); self.screen.blit(img, (SCREEN_WIDTH//2 - img.get_width()//2, 250 + i * 45))
        if self.state in [STATE_INTRO, STATE_GAME_OVER]:
            self.screen.blit(self.info_font.render("--- Top Pilots ---", True, CYAN), (SCREEN_WIDTH//2 - 80, 350))
            for i, hs in enumerate(self.highscores[:5]):
                txt = f"{i+1}. {hs['name']} - {hs['score']:07}"; self.screen.blit(self.info_font.render(txt, True, WHITE), (SCREEN_WIDTH//2 - 90, 380 + i * 22))
    def handle_highscore_transition(self):
        is_hs = self.score >= 2000 and (len(self.highscores) < 5 or self.score > self.highscores[-1]['score'])
        self.state = STATE_NAME_ENTRY if is_hs else STATE_GAME_OVER; self.menu_idx = 0
    def trigger_keyword(self, word):
        self.play_sfx('powerup')
        if word == "LIFE": self.lives = min(6, self.lives + 1); self.keyword_progress[word] = [False] * len(word)
        elif word == "ZAPP": self.zapp_y = SCREEN_HEIGHT; self.play_sfx('zap'); self.zapp_active = True; self.zapp_cooldown_timer = pygame.time.get_ticks() + 16000
        elif word == "BOOST": self.warp_timer = pygame.time.get_ticks() + WARP_DURATION_MS; self.play_sfx('warp'); self.keyword_progress[word] = [False] * len(word)
    def trigger_victory(self):
        self.state = STATE_VICTORY; self.menu_idx = 0; self.victory_timer = pygame.time.get_ticks()
        pygame.mixer.music.stop(); stage_music_path = os.path.join(self.music_path, "Stage")
        if os.path.exists(stage_music_path):
            tracks = [os.path.join(stage_music_path, f) for f in os.listdir(stage_music_path) if any(x in f for x in ["Achievement", "Cleared"])]
            if tracks: pygame.mixer.music.load(random.choice(tracks)); pygame.mixer.music.play()
    def run(self):
        while True:
            dt = self.clock.tick(60); now = pygame.time.get_ticks(); speed_mult = (3.0 if self.warp_timer > now else (0.2 if self.boss_mode and not self.boss_intro_done else 1.0))
            if self.state == STATE_PLAYING and not pygame.mixer.music.get_busy(): self.play_next_track(self.boss_mode)
            off = (random.randint(-self.shake, self.shake), random.randint(-self.shake, self.shake)) if self.shake > 0 else (0,0); (self.shake > 0 and setattr(self, 'shake', self.shake - 1))
            self.screen.fill(BLACK)
            for s in self.stars: s[1] = (s[1] + s[2] * speed_mult) % SCREEN_HEIGHT; pygame.draw.circle(self.screen, (100, 100, 120), (int(s[0]+off[0]), int(s[1]+off[1])), 1)
            for p in self.planets: p.update(speed_mult); p.draw(self.screen, off)
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.KEYDOWN:
                    if self.state == STATE_PLAYING:
                        if e.key == pygame.K_ESCAPE: self.state = STATE_PAUSED; self.menu_idx = 0; self.play_sfx('blip')
                        elif e.key == pygame.K_d and (pygame.key.get_mods() & pygame.KMOD_LSHIFT): self.distance = 9.0; self.play_sfx('warp')
                        elif e.key == pygame.K_F8:
                            cycle = ['dual', 'triple', 'blast', 'laser']; idx = (cycle.index(self.weapon) + 1) % len(cycle) if self.weapon in cycle else 0
                            self.weapon = cycle[idx]; self.weapon_tier = 1; self.play_sfx('blip')
                        elif e.key == pygame.K_F7:
                            self.weapon, self.weapon_tier = 'super_laser', 2; self.play_sfx('warp')
                        elif self.zapp_active and e.key == pygame.K_z:
                            if now > self.zapp_cooldown_timer: self.zapp_y = SCREEN_HEIGHT; self.play_sfx('zap'); self.zapp_cooldown_timer = now + 16000
                        elif not self.paused and e.key in [pygame.K_LCTRL, pygame.K_RCTRL] and self.nukes > 0:
                            self.nukes -= 1; self.shake = 20; self.create_explosion(self.ship.x+35, self.ship.y, WHITE, 50); self.play_sfx('boom_nuke')
                            if any(self.ship.rect.colliderect(p.rect) for p in self.planets): self.powerups.append(PowerUp(self.ship.x+35, self.ship.y, 'ghost'))
                            for en in self.enemies: en.hit()
                            self.enemies = [en for en in self.enemies if not (en.hp <= 0 and not en.is_unbreakable)]
                    elif self.state == STATE_NAME_ENTRY:
                        if e.key == pygame.K_UP: self.entry_name[self.entry_idx] = (self.entry_name[self.entry_idx] + 1) % len(ALLOWED_CHARS); self.play_sfx('blip')
                        elif e.key == pygame.K_DOWN: self.entry_name[self.entry_idx] = (self.entry_name[self.entry_idx] - 1) % len(ALLOWED_CHARS); self.play_sfx('blip')
                        elif e.key in [pygame.K_RETURN, pygame.K_SPACE]:
                            self.play_sfx('blip'); self.entry_idx += 1
                            if self.entry_idx > 3:
                                name = "".join([ALLOWED_CHARS[i] for i in self.entry_name]); self.highscores.append({"name": name, "score": self.score}); self.save_highscores(); self.load_highscores(); self.state = STATE_GAME_OVER
                        elif e.key == pygame.K_BACKSPACE: self.entry_idx = max(0, self.entry_idx - 1); self.play_sfx('blip')
                    elif self.state in [STATE_INTRO, STATE_PAUSED, STATE_GAME_OVER, STATE_CLEARED, STATE_CONTINUE, STATE_VICTORY]:
                        if e.key == pygame.K_UP: self.menu_idx = (self.menu_idx - 1) % self.menu_count; self.play_sfx('blip')
                        if e.key == pygame.K_DOWN: self.menu_idx = (self.menu_idx + 1) % self.menu_count; self.play_sfx('blip')
                        if e.key in [pygame.K_RETURN, pygame.K_SPACE]:
                            self.play_sfx('blip')
                            if self.state == STATE_INTRO:
                                if self.menu_idx == 0: self.state = STATE_PLAYING; self.reset_game(True)
                                else: pygame.quit(); sys.exit()
                            elif self.state == STATE_PAUSED:
                                if self.menu_idx == 0: self.state = STATE_PLAYING
                                else: self.state = STATE_INTRO; pygame.mixer.music.stop()
                            elif self.state == STATE_CONTINUE:
                                if self.menu_idx == 0: self.score, self.lives = 0, 3; self.reset_game(False); self.ship.reset(True); self.state = STATE_PLAYING
                                else: self.handle_highscore_transition()
                            elif self.state in [STATE_GAME_OVER, STATE_CLEARED, STATE_VICTORY]:
                                if self.menu_idx == 0: self.state = STATE_PLAYING; self.reset_game(True)
                                else: self.state = STATE_INTRO
                        if self.state == STATE_PAUSED and e.key == pygame.K_ESCAPE: self.state = STATE_PLAYING
            
            # Particles move regardless of world freeze
            for part in self.particles[:]: 
                part.update(); part.draw(self.screen)
                if part.life <= 0: self.particles.remove(part)

            if self.state == STATE_PLAYING or self.state == STATE_PAUSED:
                if not self.paused and self.state == STATE_PLAYING:
                    self.frames += 1; (self.distance < self.target_distance and setattr(self, 'distance', self.distance + (dt / AU_TIME_MS) * speed_mult))
                    if self.distance >= BOSS_TRIGGER_AU and not self.boss_mode: self.boss_mode = True; pygame.mixer.music.fadeout(2000); self.bosses = [BossPlanet(200, 0), BossPlanet(600, 1)]; self.flare_timer = now + 10000
                    if self.boss_mode and all(b.alpha >= 255 for b in self.bosses): self.boss_intro_done = True
                    ks = pygame.key.get_pressed(); self.ship.move(ks); (self.ship.x, self.ship.y) != self.last_ship_pos and (setattr(self, 'idle_timer', now) or setattr(self, 'last_ship_pos', (self.ship.x, self.ship.y)))
                    if now - self.idle_timer > IDLE_LIMIT_MS: self.enemies.append(Enemy(is_comet=True, target_pos=(self.ship.x+35, self.ship.y+40))); self.idle_timer = now; self.play_sfx('warning')
                    if not self.ship.is_entering and ks[pygame.K_SPACE]: self.fire()
                    spawn_prob = (0.02 + (self.stage * 0.006)); spawn_prob *= (1.3 if self.distance >= 8.0 else (1.2 if self.distance >= 6.0 else 1.0))
                    if random.random() < spawn_prob * speed_mult and not self.boss_mode:
                        if random.random() < 0.05 and not any(en.is_unbreakable for en in self.enemies): self.enemies.append(Enemy(is_unbreakable=True))
                        else: self.enemies.append(Enemy(is_tank=random.random() < 0.12))
                    if self.zapp_y is not None:
                        self.zapp_y -= 5; pygame.draw.rect(self.screen, WHITE, (0, self.zapp_y, SCREEN_WIDTH, 20))
                        for b in self.bosses: (not b.is_dying and b.rect.colliderect(pygame.Rect(0, self.zapp_y, SCREEN_WIDTH, 20)) and setattr(b, 'hp', b.hp - 0.5))
                        if self.zapp_y < -20: self.zapp_y = None
                    if self.boss_mode:
                        active_bosses = [b for b in self.bosses if not b.is_dying]
                        if len(active_bosses) == 2 and active_bosses[0].rect.colliderect(active_bosses[1].rect):
                            self.play_sfx('boss_impact'); self.shake = 15; pygame.draw.rect(self.screen, WHITE, (0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
                            self.boss_bullets.append(BossProjectile(active_bosses[0].x, active_bosses[0].y, 0, 8, 40, WHITE))
                            for _ in range(3): self.enemies.append(Enemy(is_comet=True, target_pos=(self.ship.x+35, self.ship.y+40)))
                            for b in active_bosses: b.vx *= -1; b.x += b.vx * 10
                        if now > self.flare_timer and active_bosses:
                            b = random.choice(active_bosses); b.shake_timer = 90; self.flare_timer = now + 10000
                            for a in range(0, 360, 15): rad = math.radians(a); self.boss_bullets.append(BossProjectile(b.x, b.y, math.cos(rad)*4, math.sin(rad)*4, 15, ORANGE))
                    for b in self.bullets[:]:
                        b.update(speed_mult); b.draw(self.screen)
                        if b.y < -100 or b.y > SCREEN_HEIGHT + 100: self.bullets.remove(b)
                        else:
                            for en in self.enemies[:]:
                                if en.rect.colliderect(b.rect):
                                    if 'laser' not in b.w_key: (b in self.bullets and self.bullets.remove(b))
                                    self.create_explosion(b.x, b.y, b.config['color'], 5); self.play_sfx('hit_tank' if (en.is_tank or en.is_unbreakable or en.is_comet) else 'hit_normal')
                                    if en.is_unbreakable: self.unbreakable_hits += 1
                                    elif en.is_tank: (self.unbreakable_hits < 10 and setattr(self, 'unbreakable_hits', 0))
                                    else: self.unbreakable_hits = 0
                                    if en.hit():
                                        self.create_explosion(en.x, en.y, en.color, 20); self.play_sfx('boom_tank' if en.is_tank else 'boom_normal'); self.score += 150 if en.is_tank else 25
                                        if en.is_tank and self.unbreakable_hits >= 10: self.powerups.append(PowerUp(en.x, en.y, 'drone')); self.unbreakable_hits = 0
                                        if random.random() < 0.1:
                                            needed_words = [w for w, p in self.keyword_progress.items() if (False in p or (w == "ZAPP" and not self.zapp_active))]
                                            if needed_words:
                                                word = random.choice(needed_words); missing = [i for i, val in enumerate(self.keyword_progress[word]) if not val]
                                                if missing: self.letters.append(LetterItem(en.x, en.y, word[random.choice(missing)]))
                                        if random.random() < 0.18: self.powerups.append(PowerUp(en.x, en.y, 'nuke' if random.random() < 0.25 else random.choice(list(WEAPONS.keys())[1:5])))
                                        self.enemies.remove(en)
                                    break
                            for bo in self.bosses[:]:
                                if not bo.is_dying and bo.rect.colliderect(b.rect):
                                    if 'laser' not in b.w_key: (b in self.bullets and self.bullets.remove(b))
                                    bo.hp -= 1; self.play_sfx('hit_tank'); self.boss_hits_received += 1; bo.shake_timer = 5
                                    if self.boss_hits_received % 60 == 0: self.powerups.append(PowerUp(bo.x, bo.y, random.choice(list(WEAPONS.keys())[1:5])))
                                    if self.boss_hits_received % 120 == 0: self.powerups.append(PowerUp(bo.x, bo.y, 'nuke'))
                                    if bo.hp <= 0:
                                        bo.is_dying, bo.death_timer = True, now; self.score += 5000
                                        remaining = [b for b in self.bosses if not b.is_dying]
                                        if len(remaining) == 1: remaining[0].is_rage = True
                                    break
                            for bb in self.boss_bullets[:]:
                                if bb.rect.colliderect(b.rect):
                                    if 'laser' not in b.w_key: (b in self.bullets and self.bullets.remove(b))
                                    self.create_explosion(bb.x, bb.y, bb.color, 10); self.play_sfx('blip'); self.boss_bullets.remove(bb); break
                    for bo in self.bosses[:]:
                        res = bo.update(); (res == "shockwave" and self.boss_bullets.append(BossProjectile(bo.x, bo.y, 0, 8, 40, WHITE)))
                        bo.draw(self.screen, self.info_font)
                        if bo.is_dying and now - bo.death_timer > 1000:
                            self.create_explosion(bo.x, bo.y, RED, 100, 3.0); self.play_sfx('boom_ship'); self.bosses.remove(bo)
                            if not self.bosses: self.trigger_victory()
                    for en in self.enemies[:]:
                        en.update(self.particles, speed_mult); en.draw(self.screen)
                        if (self.zapp_y is not None and en.y > self.zapp_y) or (self.warp_timer > now and en.rect.colliderect(self.ship.rect)): self.create_explosion(en.x, en.y, WHITE, 10); self.enemies.remove(en); self.score += 50; continue
                        if en.y > SCREEN_HEIGHT + 100: self.enemies.remove(en)
                        elif not self.ship.is_invulnerable(self.warp_timer > now) and en.rect.colliderect(self.ship.rect):
                            self.lives -= 1; self.shake = 25; self.impact_flash = now + 100; self.hit_shockwave = 0
                            if self.lives <= 0: self.state = STATE_DEATH_SEQUENCE; self.death_timer = now; self.killer_enemy = en; pygame.mixer.music.stop()
                            else: self.create_explosion(self.ship.x+35, self.ship.y+40, RED, 40); self.play_sfx('boom_ship'); self.paused = True; self.pause_time = now; self.enemies.remove(en)
                    for bb in self.boss_bullets[:]:
                        bb.update(); bb.draw(self.screen)
                        if bb.rect.colliderect(self.ship.rect) and not self.ship.is_invulnerable(self.warp_timer > now):
                            self.lives -= 1; self.shake = 25; self.impact_flash = now + 100; self.hit_shockwave = 0
                            if self.lives <= 0: self.state = STATE_DEATH_SEQUENCE; self.death_timer = now; pygame.mixer.music.stop()
                            else: (bb in self.boss_bullets and self.boss_bullets.remove(bb)); self.paused = True; self.pause_time = now
                        elif bb.y > SCREEN_HEIGHT + 50 or bb.y < -50 or bb.x < -50 or bb.x > SCREEN_WIDTH + 50: (bb in self.boss_bullets and self.boss_bullets.remove(bb))
                    for p in self.powerups[:]:
                        p.update(); p.draw(self.screen)
                        if p.rect.colliderect(self.ship.rect):
                            self.play_sfx('powerup')
                            if p.p_type == 'nuke': self.nukes += 1
                            elif p.p_type == 'drone': self.drone_timer = now + DRONE_DURATION_MS
                            elif p.p_type == 'ghost': self.ghost_fires = GHOST_MAX_FIRES
                            else:
                                if self.weapon == p.p_type:
                                    if self.weapon == 'laser': self.weapon, self.weapon_tier = 'super_laser', 2
                                    elif self.weapon_tier < 2: self.weapon_tier = 2
                                    else:
                                        cx, cy = self.ship.x + 35, self.ship.y
                                        self.mortars.extend([Mortar(cx, cy, -5, -5), Mortar(cx, cy, 5, -5)]); self.play_sfx('boom_nuke')
                                elif self.weapon == 'super_laser' and p.p_type == 'laser':
                                    cx, cy = self.ship.x + 35, self.ship.y
                                    self.mortars.extend([Mortar(cx, cy, -5, -5), Mortar(cx, cy, 5, -5)]); self.play_sfx('boom_nuke')
                                else: self.weapon, self.weapon_tier = p.p_type, 1
                            self.powerups.remove(p)
                        elif p.y > SCREEN_HEIGHT: self.powerups.remove(p)
                    for m in self.mortars[:]:
                        m.update(); pygame.draw.circle(self.screen, ORANGE, (int(m.x), int(m.y)), 10); pygame.draw.circle(self.screen, WHITE, (int(m.x), int(m.y)), 6)
                        if m.detonated:
                            self.create_explosion(m.x, m.y, WHITE, 60, 4.0); self.play_sfx('boom_tank'); exp_rect = pygame.Rect(m.x-80, m.y-80, 160, 160)
                            for en in self.enemies[:]: (exp_rect.colliderect(en.rect) and en.hit() and (setattr(self, 'score', self.score+50) or self.enemies.remove(en)))
                            for bb in self.boss_bullets[:]: (exp_rect.collidepoint(bb.x, bb.y) and self.boss_bullets.remove(bb))
                            for bo in self.bosses: (not bo.is_dying and exp_rect.colliderect(bo.rect) and setattr(bo, 'hp', bo.hp - 10) or setattr(bo, 'shake_timer', 10))
                            self.mortars.remove(m)
                    for l in self.letters[:]:
                        l.update(); l.draw(self.screen, self.misa_font)
                        if l.rect.colliderect(self.ship.rect):
                            for w, pr in self.keyword_progress.items():
                                if l.char in w:
                                    for i in range(len(w)):
                                        if w[i] == l.char and not pr[i]: pr[i] = True; (all(pr) and self.trigger_keyword(w)); break
                                    else: continue
                                    break
                            self.play_sfx('blip'); self.letters.remove(l)
                        elif l.y > SCREEN_HEIGHT: self.letters.remove(l)
                    (self.drone_timer > now and (self.draw_drones() or pygame.draw.rect(self.screen, PURPLE, (SCREEN_WIDTH - 110, SCREEN_HEIGHT - 20, 100 * ((self.drone_timer - now) / DRONE_DURATION_MS), 5))))
                    (self.ghost_fires > 0 and self.draw_ghost()); self.ship.draw(self.screen, warp=(self.warp_timer > now))
                    if self.ship.is_entering:
                        rem = 3 - ((now - self.ship_ready_time) // 1000)
                        if rem > 0: self.screen.blit(self.countdown_font.render(str(rem), True, YELLOW), (SCREEN_WIDTH//2 - 15, SCREEN_HEIGHT//2 - 50))
                        else: self.ship.is_entering = False; self.ship.invulnerable_until = now + 2000 
                else:
                    # DRAW FROZEN WORLD
                    for b in self.bullets: b.draw(self.screen)
                    for en in self.enemies: en.draw(self.screen)
                    for bo in self.bosses: bo.draw(self.screen, self.info_font)
                    for bb in self.boss_bullets: bb.draw(self.screen)
                    for p in self.powerups: p.draw(self.screen)
                    for l in self.letters: l.draw(self.screen, self.misa_font)
                    self.ship.draw(self.screen, warp=(self.warp_timer > now), strobe=self.paused)
                    # Impact Flash & Shockwave logic
                    if self.impact_flash > now: 
                        flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); flash.fill(RED); flash.set_alpha(100); self.screen.blit(flash, (0,0))
                        self.hit_shockwave += 10; pygame.draw.circle(self.screen, WHITE, self.ship.rect.center, self.hit_shockwave, 3)
                    if self.state == STATE_PLAYING and self.paused:
                        if now - self.pause_time > 1800: self.paused = False; self.ship.reset(True); self.ship_ready_time = now
            elif self.state == STATE_DEATH_SEQUENCE:
                el = now - self.death_timer
                if el < 1000: ((el // 50) % 2 == 0 and self.ship.draw(self.screen, 255)) or self.ship.draw(self.screen, 100); (self.killer_enemy and self.killer_enemy.draw(self.screen)); setattr(self, 'shake', 5)
                elif el < 2500:
                    if el < 1100: self.play_sfx('boom_ship'); self.shake = 30; self.create_explosion(self.ship.x+35, self.ship.y+40, CYAN, 60, 4.0); self.create_explosion(self.ship.x+35, self.ship.y+40, WHITE, 40, 2.0)
                    if 1500 < el < 1600: self.create_explosion(self.ship.x+35, self.ship.y+40, ORANGE, 80, 5.0); self.shake = 40
                    if 2000 < el < 2100: self.create_explosion(self.ship.x+35, self.ship.y+40, RED, 100, 6.0); self.play_sfx('game_over')
                    (self.killer_enemy and self.killer_enemy.draw(self.screen))
                else:
                    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); fade.fill((50, 0, 0, min(255, (el - 2500) // 4))); self.screen.blit(fade, (0,0))
                    if el > 4000: self.state = STATE_CONTINUE; self.continue_timer = now; self.menu_idx = 0
            elif self.state == STATE_CONTINUE:
                rem = 10 - ((now - self.continue_timer) // 1000)
                if rem <= 0: self.handle_highscore_transition()
                else: self.menu_count = 2; self.draw_menu_overlay(f"Continue? {rem}", ["YES", "NO"], YELLOW, small_title=True)
            elif self.state == STATE_NAME_ENTRY:
                ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); ov.fill((0, 0, 0, 200)); self.screen.blit(ov, (0,0))
                self.screen.blit(self.info_font.render("New High Score!", True, YELLOW), (SCREEN_WIDTH//2-80, 100))
                self.screen.blit(self.info_font.render(f"Score: {self.score:07}", True, WHITE), (SCREEN_WIDTH//2-80, 180))
                self.screen.blit(self.info_font.render("Enter Initials (4 Chars)", True, CYAN), (SCREEN_WIDTH//2-120, 250))
                for i in range(4):
                    char = ALLOWED_CHARS[self.entry_name[i]]; color = YELLOW if i == self.entry_idx else WHITE; img = self.info_font.render(char, True, color); self.screen.blit(img, (SCREEN_WIDTH//2 - 60 + i * 35, 320))
                    if i == self.entry_idx: pygame.draw.line(self.screen, YELLOW, (SCREEN_WIDTH//2 - 60 + i * 35, 345), (SCREEN_WIDTH//2 - 40 + i * 35, 345), 2)
                self.screen.blit(self.info_font.render("Up/Down to Cycle - Fire to Confirm - Bksp to Correct", True, DARK_GRAY), (SCREEN_WIDTH//2-220, 450))
            elif self.state == STATE_VICTORY:
                el = now - self.victory_timer
                if el < 1000 and (el // 200) % 2 == 0: self.screen.fill(WHITE)
                if random.random() < 0.15:
                    fx, fy = random.randint(50, SCREEN_WIDTH-50), random.randint(50, SCREEN_HEIGHT-250)
                    col = random.choice([CYAN, YELLOW, PURPLE, GREEN, ORANGE, WHITE, RED]); self.create_explosion(fx, fy, col, count=40, speed=4.0); self.play_sfx('blip')
                if self.ship.y > -100:
                    self.ship.y -= 8; (random.random() < 0.5 and self.particles.append(Particle(self.ship.x+35, self.ship.y+80, random.choice([CYAN, WHITE]), vy=5)))
                self.ship.draw(self.screen)
                if el > 2500: self.menu_count = 2; self.draw_menu_overlay("Mission Accomplished!", ["REPLAY MISSION", "QUIT TO MENU"], YELLOW)
            
            if self.state not in [STATE_INTRO, STATE_DEATH_SEQUENCE, STATE_NAME_ENTRY, STATE_CONTINUE, STATE_VICTORY]:
                ui_y = 10; w_label = self.weapon.capitalize().replace("Super_laser", "Super Laser") + (" [Max]" if self.weapon_tier > 1 else ""); labels = [f"Score: {self.score:07}", f"Stage: {self.stage}", f"Nukes: {self.nukes}", f"Weapon: {w_label}", f"Dist: {self.distance:05.2f} / {self.target_distance:05.2f} Au"]
                for label in labels: self.screen.blit(self.info_font.render(label, True, WHITE if "Dist" not in label else CYAN), (10, ui_y)); ui_y += 22
                draw_arcade_symbol(self.screen, 185, 95, self.weapon, WEAPONS[self.weapon]['color'], 8, False); [draw_pixel_heart(self.screen, RED, SCREEN_WIDTH - 25 - i*30, 25, 25) for i in range(max(0, self.lives))]
                ky = 60
                for word, progress in self.keyword_progress.items():
                    full_w = sum([self.misa_font.size(c)[0] for c in word]); start_x = SCREEN_WIDTH - 20 - full_w; current_x = start_x
                    if word == "ZAPP" and self.zapp_active:
                        elapsed = max(0, 16000 - (self.zapp_cooldown_timer - now)); green_count = elapsed // 4000
                        for i, char in enumerate(word): char_w = self.misa_font.size(char)[0]; color = GREEN if i < green_count else RED; self.screen.blit(self.misa_font.render(char, True, color), (current_x, ky)); current_x += char_w
                    else:
                        for i, char in enumerate(word):
                            char_w = self.misa_font.size(char)[0]
                            if progress[i]: self.screen.blit(self.misa_font.render(char, True, GREEN if all(progress) else WHITE), (current_x, ky))
                            current_x += char_w
                    ky += 35
                (self.warp_timer > now and pygame.draw.rect(self.screen, CYAN, (SCREEN_WIDTH - 110, ky + 10, 100 * ((self.warp_timer - now) / WARP_DURATION_MS), 4)))
                if self.ghost_fires > 0: img = self.info_font.render(f"Ghost Ammo: {self.ghost_fires}", True, CYAN); self.screen.blit(img, (SCREEN_WIDTH - 20 - img.get_width(), SCREEN_HEIGHT - 40))
            
            if self.state == STATE_INTRO: self.menu_count = 2; self.draw_menu_overlay("ULTRA SPACE ARCADE", ["START MISSION", "QUIT GAME"], BLUE)
            elif self.state == STATE_PAUSED: self.menu_count = 2; self.draw_menu_overlay("MISSION PAUSED", ["RESUME", "ABANDON MISSION"], CYAN)
            elif self.state == STATE_GAME_OVER: self.menu_count = 2; self.draw_menu_overlay("MISSION FAILED", ["TRY AGAIN", "QUIT TO MENU"], RED)
            elif self.state == STATE_CLEARED: self.menu_count = 2; self.draw_menu_overlay("STAGE CLEARED", ["NEXT MISSION", "QUIT TO MENU"], GREEN)
            pygame.display.flip()

    def draw_drones(self): draw_arcade_symbol(self.screen, int(self.ship.x - 40), int(self.ship.y + 20), 'drone', PURPLE, 12); draw_arcade_symbol(self.screen, int(self.ship.x + 110), int(self.ship.y + 20), 'drone', PURPLE, 12)
    def draw_ghost(self): gx = SCREEN_WIDTH - self.ship.x - self.ship.width; ay_s, ay_e = SCREEN_HEIGHT // 2, SCREEN_HEIGHT - self.ship.height; gy = ay_s + (ay_e - self.ship.y); alpha = int(120 + 100 * math.sin(pygame.time.get_ticks() * 0.01)); draw_pixel_heart(self.screen, RED, gx + 12, gy + self.ship.height - 20, 35, True, alpha // 2); draw_pixel_heart(self.screen, RED, gx + self.ship.width - 12, gy + self.ship.height - 20, 35, True, alpha // 2); draw_pixel_heart(self.screen, GHOST_COLOR, gx + 35, gy + 40, 75, True, alpha); draw_pixel_heart(self.screen, CYAN, gx + 35, gy + 28, 18, False, alpha)
    def ghost_fire(self):
        gx = SCREEN_WIDTH - self.ship.x - self.ship.width; ay_s, ay_e = SCREEN_HEIGHT // 2, SCREEN_HEIGHT - self.ship.height; gy = ay_s + (ay_e - self.ship.y); cx, y = gx + self.ship.width//2, gy
        if self.weapon == 'normal': self.bullets.append(Bullet(cx, y, 'ghost_normal', color=GHOST_COLOR))
        elif self.weapon == 'dual': self.bullets.extend([Bullet(cx-18, y-10, 'ghost_dual', color=GHOST_COLOR), Bullet(cx+18, y-10, 'ghost_dual', color=GHOST_COLOR)])
        elif self.weapon == 'triple': [self.bullets.append(Bullet(cx, y, 'ghost_triple', a, color=GHOST_COLOR)) for a in [0, -0.25, 0.25]]
        elif self.weapon == 'laser' or self.weapon == 'super_laser': self.bullets.append(Bullet(cx, y, 'ghost_laser', color=GHOST_COLOR))
        elif self.weapon == 'blast': [self.bullets.append(Bullet(cx, y, 'ghost_blast', orbit_angle=ang, color=GHOST_COLOR)) for ang in [0, 2.094, 4.188]]
    def fire(self):
        now = pygame.time.get_ticks()
        base_rate = WEAPONS[self.weapon]['rate']
        actual_rate = base_rate // 2 if (self.weapon_tier > 1 and self.weapon not in ['laser', 'super_laser']) else base_rate
        if now - self.last_fire < actual_rate: return
        self.last_fire = now; self.play_sfx(WEAPONS[self.weapon]['sound']); cx, y = self.ship.x + self.ship.width//2, self.ship.y
        if self.weapon == 'normal': self.bullets.append(Bullet(cx, y, 'normal'))
        elif self.weapon == 'dual': self.bullets.extend([Bullet(cx-18, y+10, 'dual'), Bullet(cx+18, y+10, 'dual')])
        elif self.weapon == 'triple': [self.bullets.append(Bullet(cx, y, 'triple', a)) for a in [0, -0.25, 0.25]]
        elif self.weapon == 'laser':
            if self.weapon_tier > 1: self.bullets.extend([Bullet(cx-12, y, 'super_laser'), Bullet(cx+12, y, 'super_laser')])
            else: self.bullets.append(Bullet(cx, y, 'laser'))
        elif self.weapon == 'blast': [self.bullets.append(Bullet(cx, y, 'blast', orbit_angle=ang)) for ang in [0, 2.094, 4.188]]; self.shake = 3
        elif self.weapon == 'super_laser':
            offset = -15 if self.super_laser_toggle else 15
            self.bullets.append(Bullet(cx + offset, y, 'super_laser'))
            self.super_laser_toggle = not self.super_laser_toggle
        if self.drone_timer > now:
            self.bullets.append(Bullet(self.ship.x - 40, self.ship.y + 20, 'drone_laser', angle=0.26, color=PURPLE))
            self.bullets.append(Bullet(self.ship.x + 110, self.ship.y + 20, 'drone_laser', angle=-0.26, color=PURPLE))
        if self.ghost_fires > 0: self.ghost_fire(); self.ghost_fires -= 1
if __name__ == "__main__":
    try: Game().run()
    except Exception as e: import traceback; traceback.print_exc(); input("Press Enter to exit...")
