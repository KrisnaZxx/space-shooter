import pygame
import random
import sys
import os

pygame.init()

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 255, 0)
RED    = (220, 50,  50)
GREEN  = (50,  220, 100)
GRAY   = (150, 150, 150)
CYAN   = (0,   255, 255)
ORANGE = (255, 165, 0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()

font_large = pygame.font.SysFont("arial", 48, bold=True)
font_mid   = pygame.font.SysFont("arial", 28)
font_small = pygame.font.SysFont("arial", 20)

# Load asset
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

def load_sprite(filename, crop, scale=None):
    path   = os.path.join(ASSET_DIR, filename)
    sheet  = pygame.image.load(path).convert_alpha()
    x, y, w, h = crop
    sprite = sheet.subsurface(pygame.Rect(x, y, w, h))
    if scale:
        sprite = pygame.transform.scale(sprite, scale)
    return sprite

def load_background(filename, target_w, target_h):
    path = os.path.join(ASSET_DIR, filename)
    img  = pygame.image.load(path).convert()
    return pygame.transform.scale(img, (target_w, target_h))

try:
    IMG_PLAYER = [
        load_sprite("SpaceShips_Player-0001.png", (12,  22, 39, 41), (58, 62)),
        load_sprite("SpaceShips_Player-0001.png", (76,  22, 39, 41), (58, 62)),
        load_sprite("SpaceShips_Player-0001.png", (140, 22, 39, 41), (58, 62)),
        load_sprite("SpaceShips_Player-0001.png", (204, 22, 39, 41), (58, 62)),
    ]
    IMG_ENEMY_BIG = [
        load_sprite("SpaceShips_Enemy-0001.png", (33, 10,  47, 54), (56, 64)),
        load_sprite("SpaceShips_Enemy-0001.png", (33, 97,  47, 56), (56, 64)),
        load_sprite("SpaceShips_Enemy-0001.png", (33, 187, 47, 53), (56, 64)),
    ]
    IMG_ASTEROID = [
        load_sprite("Asteroids-0001.png", (6,  30, 50, 32), (52, 52)),
        load_sprite("Asteroids-0001.png", (6,  69, 39, 38), (52, 52)),
        load_sprite("Asteroids-0001.png", (83, 16, 29, 45), (34, 34)),
        load_sprite("Asteroids-0001.png", (70, 69, 39, 38), (34, 34)),
    ]
    IMG_BG = load_background("Background_Full-0001.png", SCREEN_WIDTH, SCREEN_HEIGHT)
    ASSETS_LOADED = True
except Exception as e:
    print(f"[WARNING] Asset tidak ditemukan: {e}")
    ASSETS_LOADED   = False
    IMG_PLAYER      = None
    IMG_ENEMY_BIG   = None
    IMG_ASTEROID    = None
    IMG_BG          = None


# Base class (Parent)
class GameObject:
    def __init__(self, x, y, width, height, color):  # Constructor
        self.__x      = x
        self.__y      = y
        self.__width  = width
        self.__height = height
        self.__color  = color
        self.__active = True

    # Getter
    def get_x(self):      return self.__x
    def get_y(self):      return self.__y
    def get_width(self):  return self.__width
    def get_height(self): return self.__height
    def get_color(self):  return self.__color
    def is_active(self):  return self.__active

    # Setter
    def set_x(self, x):         self.__x = x
    def set_y(self, y):         self.__y = y
    def set_color(self, color): self.__color = color
    def set_active(self, val):  self.__active = val

    def get_rect(self):
        return pygame.Rect(self.__x, self.__y, self.__width, self.__height)

    def draw(self, surface): pass
    def update(self):        pass

    def __del__(self): pass  # Destructor


# Inheritance: Player -> GameObject
class Player(GameObject):
    def __init__(self, x, y, skin=1):
        super().__init__(x, y, 58, 62, CYAN)
        self.__speed          = 5
        self.__health         = 100
        self.__max_health     = 100
        self.__score          = 0
        self.__shoot_cooldown = 0
        self.__shoot_delay    = 15
        self.__invincible     = 0
        self.__bullets        = []
        self.__skin           = skin

    # Getter
    def get_health(self):     return self.__health
    def get_max_health(self): return self.__max_health
    def get_score(self):      return self.__score
    def get_bullets(self):    return self.__bullets

    # Setter
    def set_health(self, val): self.__health = max(0, min(val, self.__max_health))
    def add_score(self, val):  self.__score += val

    def shoot(self):
        if self.__shoot_cooldown <= 0:
            cx = self.get_x() + self.get_width() // 2 - 3
            self.__bullets.append(Bullet(cx, self.get_y(), speed=11, color=CYAN, direction=-1))
            self.__shoot_cooldown = self.__shoot_delay

    def take_damage(self, amount):
        if self.__invincible <= 0:
            self.__health -= amount
            self.__invincible = 60
            if self.__health <= 0:
                self.__health = 0
                self.set_active(False)

    def update(self, keys):
        x, y = self.get_x(), self.get_y()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: x -= self.__speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: x += self.__speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: y -= self.__speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: y += self.__speed
        x = max(0, min(x, SCREEN_WIDTH  - self.get_width()))
        y = max(0, min(y, SCREEN_HEIGHT - self.get_height()))
        self.set_x(x)
        self.set_y(y)
        if self.__shoot_cooldown > 0: self.__shoot_cooldown -= 1
        if self.__invincible     > 0: self.__invincible     -= 1
        for b in self.__bullets: b.update()
        self.__bullets = [b for b in self.__bullets if b.is_active()]

    def draw(self, surface):  # Method override
        if self.__invincible > 0 and (self.__invincible // 5) % 2 == 0:
            return
        x, y = self.get_x(), self.get_y()
        w, h = self.get_width(), self.get_height()
        if ASSETS_LOADED and IMG_PLAYER:
            surface.blit(IMG_PLAYER[self.__skin], (x, y))
        else:
            pygame.draw.polygon(surface, CYAN, [(x + w//2, y), (x, y + h), (x + w, y + h)])
        # Health bar
        bx, by = x, y + h + 5
        pygame.draw.rect(surface, (60, 60, 60), (bx, by, w, 5))
        ratio = self.__health / self.__max_health
        c = GREEN if ratio > 0.5 else YELLOW if ratio > 0.25 else RED
        pygame.draw.rect(surface, c, (bx, by, int(w * ratio), 5))
        for b in self.__bullets:
            b.draw(surface)


# Inheritance: Bullet -> GameObject
class Bullet(GameObject):
    def __init__(self, x, y, speed=11, color=CYAN, direction=-1):
        super().__init__(x, y, 6, 16, color)
        self.__speed     = speed
        self.__direction = direction  # -1 ke atas, +1 ke bawah

    def update(self):  # Method override
        self.set_y(self.get_y() + self.__speed * self.__direction)
        if self.get_y() < -20 or self.get_y() > SCREEN_HEIGHT + 20:
            self.set_active(False)

    def draw(self, surface):  # Method override
        x, y = self.get_x(), self.get_y()
        w, h = self.get_width(), self.get_height()
        pygame.draw.rect(surface, self.get_color(), (x, y, w, h), border_radius=3)
        pygame.draw.rect(surface, WHITE, (x + 1, y + 1, w - 2, 4), border_radius=2)


# Inheritance: Enemy -> GameObject
class Enemy(GameObject):
    def __init__(self, x, y, width, height, color, health, speed):
        super().__init__(x, y, width, height, color)
        self.__health     = health
        self.__max_health = health
        self.__speed      = speed
        self.__bullets    = []

    # Getter
    def get_enemy_health(self):  return self.__health
    def get_max_health(self):    return self.__max_health
    def get_speed(self):         return self.__speed
    def get_enemy_bullets(self): return self.__bullets

    def take_damage(self, amount):
        self.__health -= amount
        if self.__health <= 0:
            self.set_active(False)

    def _add_bullet(self, bullet):
        self.__bullets.append(bullet)

    def update(self):
        self.set_y(self.get_y() + self.__speed)
        if self.get_y() > SCREEN_HEIGHT + 60:
            self.set_active(False)
        for b in self.__bullets: b.update()
        self.__bullets = [b for b in self.__bullets if b.is_active()]

    def draw(self, surface): pass  # di-override child class


# Inheritance: Asteroid -> Enemy -> GameObject
class Asteroid(Enemy):
    def __init__(self, x, y):
        self.__variant = random.randint(0, 1)
        speed = random.uniform(1.5, 3.2)
        super().__init__(x, y, 52, 52, GRAY, health=2, speed=speed)
        self.__rot       = random.randint(0, 360)
        self.__rot_speed = random.uniform(-2.5, 2.5)
        self.__img       = IMG_ASTEROID[self.__variant] if ASSETS_LOADED else None

    def update(self):  # Method override
        super().update()
        self.__rot += self.__rot_speed

    def draw(self, surface):  # Method override
        x, y = self.get_x(), self.get_y()
        cx   = x + self.get_width()  // 2
        cy   = y + self.get_height() // 2
        if self.__img:
            rotated = pygame.transform.rotate(self.__img, self.__rot)
            rect    = rotated.get_rect(center=(cx, cy))
            surface.blit(rotated, rect.topleft)
        else:
            pygame.draw.circle(surface, GRAY, (cx, cy), self.get_width() // 2)


# Inheritance: AlienShip -> Enemy -> GameObject
class AlienShip(Enemy):
    def __init__(self, x, y):
        self.__variant = random.randint(0, 2)
        super().__init__(x, y, 56, 64, RED, health=5, speed=1.2)
        self.__move_timer    = 0
        self.__move_dir      = random.choice([-1, 1])
        self.__lateral_speed = 2
        self.__shoot_timer   = random.randint(60, 120)
        self.__img = (pygame.transform.flip(IMG_ENEMY_BIG[self.__variant], False, True)
                      if ASSETS_LOADED else None)

    def update(self):  # Method override
        self.__move_timer += 1
        if self.__move_timer > 55:
            self.__move_dir  *= -1
            self.__move_timer = 0
        nx = self.get_x() + self.__lateral_speed * self.__move_dir
        nx = max(0, min(nx, SCREEN_WIDTH - self.get_width()))
        self.set_x(nx)
        self.__shoot_timer -= 1
        if self.__shoot_timer <= 0:
            cx = self.get_x() + self.get_width() // 2 - 3
            by = self.get_y() + self.get_height()
            self._add_bullet(Bullet(cx, by, speed=5, color=ORANGE, direction=1))
            self.__shoot_timer = random.randint(80, 140)
        super().update()

    def draw(self, surface):  # Method override
        x, y = self.get_x(), self.get_y()
        w, h = self.get_width(), self.get_height()
        if self.__img:
            surface.blit(self.__img, (x, y))
        else:
            pygame.draw.rect(surface, RED, (x, y, w, h), border_radius=8)
        # Health bar
        pygame.draw.rect(surface, (60, 60, 60), (x, y - 9, w, 5))
        ratio = self.get_enemy_health() / self.get_max_health()
        pygame.draw.rect(surface, RED, (x, y - 9, int(w * ratio), 5))
        for b in self.get_enemy_bullets():
            b.draw(surface)


# Inheritance: PowerUp -> GameObject
class PowerUp(GameObject):
    TYPES = ["health", "rapid_fire"]

    def __init__(self, x, y):
        self.__type  = random.choice(self.TYPES)
        color        = GREEN if self.__type == "health" else YELLOW
        super().__init__(x, y, 26, 26, color)
        self.__speed     = 2
        self.__bob_timer = random.uniform(0, 6.28)

    # Getter
    def get_type(self): return self.__type

    def update(self):  # Method override
        import math
        self.__bob_timer += 0.08
        self.set_y(self.get_y() + self.__speed)
        if self.get_y() > SCREEN_HEIGHT + 30:
            self.set_active(False)

    def draw(self, surface):  # Method override
        import math
        x  = self.get_x()
        y  = self.get_y() + int(math.sin(self.__bob_timer) * 4)
        w, h   = self.get_width(), self.get_height()
        color  = self.get_color()
        cx, cy = x + w // 2, y + h // 2
        pygame.draw.circle(surface, color, (cx, cy), w // 2)
        pygame.draw.circle(surface, WHITE, (cx, cy), w // 2, 1)
        if self.__type == "health":
            pygame.draw.rect(surface, WHITE, (cx - 2, y + 5,  4, h - 10))
            pygame.draw.rect(surface, WHITE, (x + 5,  cy - 2, w - 10, 4))
        else:
            pts = [(cx+2, y+4), (cx-4, cy), (cx+1, cy),
                   (cx-2, y+h-4), (cx+4, cy), (cx-1, cy)]
            pygame.draw.polygon(surface, WHITE, pts)


# Inheritance: Star -> GameObject
class Star(GameObject):
    def __init__(self):
        x    = random.randint(0, SCREEN_WIDTH)
        y    = random.randint(0, SCREEN_HEIGHT)
        size = random.randint(1, 3)
        super().__init__(x, y, size, size, WHITE)
        self.__speed  = random.uniform(0.4, 2.0)
        self.__bright = random.randint(80, 255)

    def update(self):  # Method override
        self.set_y(self.get_y() + self.__speed)
        if self.get_y() > SCREEN_HEIGHT:
            self.set_x(random.randint(0, SCREEN_WIDTH))
            self.set_y(0)

    def draw(self, surface):  # Method override
        b = self.__bright
        pygame.draw.circle(surface, (b, b, b),
                           (int(self.get_x()), int(self.get_y())),
                           self.get_width())


class Game:
    def __init__(self):
        self.__player          = Player(SCREEN_WIDTH // 2 - 29, SCREEN_HEIGHT - 110, skin=1)
        self.__enemies         = []
        self.__powerups        = []
        self.__stars           = [Star() for _ in range(70)]
        self.__spawn_timer     = 0
        self.__spawn_rate      = 60
        self.__wave            = 1
        self.__wave_timer      = 0
        self.__state           = "menu"
        self.__countdown_timer = FPS * 4
        self.__menu_selected   = 0
        self.__bg_y            = 0

    def spawn_enemy(self):
        x = random.randint(10, SCREEN_WIDTH - 70)
        if self.__wave >= 2 and random.random() < 0.35:
            self.__enemies.append(AlienShip(x, -70))
        else:
            self.__enemies.append(Asteroid(x, -60))

    def spawn_powerup(self, x, y):
        if random.random() < 0.22:
            self.__powerups.append(PowerUp(x, y))

    def check_collisions(self):
        player    = self.__player
        p_bullets = player.get_bullets()

        for enemy in self.__enemies:
            if not enemy.is_active():
                continue
            for b in p_bullets:
                if b.is_active() and b.get_rect().colliderect(enemy.get_rect()):
                    enemy.take_damage(1)
                    b.set_active(False)
                    if not enemy.is_active():
                        pts = 10 if isinstance(enemy, Asteroid) else 25
                        player.add_score(pts)
                        self.spawn_powerup(enemy.get_x(), enemy.get_y())
            if enemy.get_rect().colliderect(player.get_rect()):
                player.take_damage(20)
                enemy.set_active(False)
            if isinstance(enemy, AlienShip):
                for b in enemy.get_enemy_bullets():
                    if b.is_active() and b.get_rect().colliderect(player.get_rect()):
                        player.take_damage(15)
                        b.set_active(False)

        for p in self.__powerups:
            if p.is_active() and p.get_rect().colliderect(player.get_rect()):
                if p.get_type() == "health":
                    player.set_health(player.get_health() + 30)
                p.set_active(False)

    def draw_background(self):
        if ASSETS_LOADED and IMG_BG:
            self.__bg_y = (self.__bg_y + 0.6) % SCREEN_HEIGHT
            screen.blit(IMG_BG, (0, int(self.__bg_y) - SCREEN_HEIGHT))
            screen.blit(IMG_BG, (0, int(self.__bg_y)))
        else:
            screen.fill(BLACK)
            for s in self.__stars:
                s.draw(screen)

    def draw_hud(self):
        player = self.__player
        # Score
        score_surf = font_mid.render(f"Score: {player.get_score()}", True, WHITE)
        screen.blit(score_surf, (10, 10))
        # Wave
        wave_surf = font_mid.render(f"Wave: {self.__wave}", True, YELLOW)
        screen.blit(wave_surf, (SCREEN_WIDTH // 2 - wave_surf.get_width() // 2, 10))
        # Health bar
        hp_label = font_small.render("HP", True, GREEN)
        screen.blit(hp_label, (10, 46))
        bx, by, bw, bh = 38, 48, 150, 14
        pygame.draw.rect(screen, (50, 50, 50), (bx, by, bw, bh), border_radius=7)
        ratio = player.get_health() / player.get_max_health()
        c = GREEN if ratio > 0.5 else YELLOW if ratio > 0.25 else RED
        pygame.draw.rect(screen, c, (bx, by, int(bw * ratio), bh), border_radius=7)
        pygame.draw.rect(screen, WHITE, (bx, by, bw, bh), 1, border_radius=7)
        hp_num = font_small.render(str(player.get_health()), True, WHITE)
        screen.blit(hp_num, (bx + bw + 6, by))
        # Kontrol hint
        hint = font_small.render(
            "WASD / Arrow: Gerak   SPACE: Tembak   ESC: Keluar", True, GRAY)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 22))

    def draw_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        screen.blit(overlay, (0, 0))
        title = font_large.render("SPACE  SHOOTER", True, WHITE)
        sub   = font_small.render("Achmad Krisna Nurvian Ananda", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 110))
        screen.blit(sub,   (SCREEN_WIDTH // 2 - sub.get_width()   // 2, 168))
        pygame.draw.line(screen, WHITE,
                         (SCREEN_WIDTH // 2 - 230, 203),
                         (SCREEN_WIDTH // 2 + 230, 203), 1)
        if ASSETS_LOADED and IMG_PLAYER:
            pimg = pygame.transform.scale(IMG_PLAYER[1], (80, 86))
            screen.blit(pimg, (SCREEN_WIDTH // 2 - 40, 218))
        items     = ["  MULAI", "  KELUAR"]
        colors_on = [GREEN, RED]
        for i, item in enumerate(items):
            y        = 335 + i * 65
            selected = (i == self.__menu_selected)
            color    = colors_on[i] if selected else WHITE
            if selected:
                box = pygame.Rect(SCREEN_WIDTH // 2 - 150, y - 8, 300, 46)
                pygame.draw.rect(screen, (0, 50, 50), box, border_radius=10)
                pygame.draw.rect(screen, WHITE, box, 1, border_radius=10)
            label = font_mid.render(item, True, color)
            screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, y))
        nav = font_small.render("↑↓ / W S   Pilih     ENTER   Konfirmasi",
                                True, (100, 100, 100))
        screen.blit(nav, (SCREEN_WIDTH // 2 - nav.get_width() // 2, SCREEN_HEIGHT - 28))

    def draw_countdown(self):
        elapsed = (FPS * 4) - self.__countdown_timer
        second  = 3 - (elapsed // FPS)
        frac    = (elapsed % FPS) / FPS
        scale   = int(90 + frac * 70)
        alpha   = int(255 * (1 - frac * 0.55))
        if second > 0:
            label = str(second)
            color = {3: RED, 2: YELLOW, 1: GREEN}.get(second, WHITE)
        else:
            label = "GO!"
            color = CYAN
        surf = pygame.font.SysFont("arial", scale, bold=True).render(label, True, color)
        surf.set_alpha(alpha)
        screen.blit(surf, (SCREEN_WIDTH  // 2 - surf.get_width()  // 2,
                           SCREEN_HEIGHT // 2 - surf.get_height() // 2 - 40))
        if second > 0:
            ready = font_small.render("Bersiap...", True, GRAY)
            screen.blit(ready, (SCREEN_WIDTH // 2 - ready.get_width() // 2,
                                SCREEN_HEIGHT // 2 + 60))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        t1 = font_large.render("GAME  OVER", True, RED)
        t2 = font_mid.render(f"Score Akhir : {self.__player.get_score()}", True, WHITE)
        t3 = font_mid.render(f"Wave        : {self.__wave}", True, YELLOW)
        t4 = font_small.render("R / ENTER → Menu     ESC → Keluar", True, GRAY)
        screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, SCREEN_HEIGHT // 2 -  20))
        screen.blit(t3, (SCREEN_WIDTH // 2 - t3.get_width() // 2, SCREEN_HEIGHT // 2 +  20))
        screen.blit(t4, (SCREEN_WIDTH // 2 - t4.get_width() // 2, SCREEN_HEIGHT // 2 +  70))

    def run(self):
        running = True
        while running:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if self.__state == "menu":
                        if event.key in (pygame.K_UP,   pygame.K_w):
                            self.__menu_selected = (self.__menu_selected - 1) % 2
                        if event.key in (pygame.K_DOWN, pygame.K_s):
                            self.__menu_selected = (self.__menu_selected + 1) % 2
                        if event.key == pygame.K_RETURN:
                            if self.__menu_selected == 0:
                                self.__state           = "countdown"
                                self.__countdown_timer = FPS * 4
                            else:
                                running = False
                    if self.__state == "game_over":
                        if event.key in (pygame.K_r, pygame.K_RETURN):
                            self.__init__()

            keys = pygame.key.get_pressed()

            if self.__state == "countdown":
                self.__countdown_timer -= 1
                if self.__countdown_timer <= 0:
                    self.__state = "playing"

            elif self.__state == "playing":
                if keys[pygame.K_SPACE]:
                    self.__player.shoot()
                self.__player.update(keys)
                if not self.__player.is_active():
                    self.__state = "game_over"
                self.__spawn_timer += 1
                if self.__spawn_timer >= self.__spawn_rate:
                    self.spawn_enemy()
                    self.__spawn_timer = 0
                self.__wave_timer += 1
                if self.__wave_timer >= FPS * 15:
                    self.__wave      += 1
                    self.__wave_timer = 0
                    self.__spawn_rate = max(20, self.__spawn_rate - 7)
                for e in self.__enemies:  e.update()
                for p in self.__powerups: p.update()
                self.__enemies  = [e for e in self.__enemies  if e.is_active()]
                self.__powerups = [p for p in self.__powerups if p.is_active()]
                self.check_collisions()

            for s in self.__stars: s.update()

            self.draw_background()

            if self.__state == "menu":
                self.draw_menu()
            elif self.__state == "countdown":
                self.__player.draw(screen)
                self.draw_countdown()
            elif self.__state == "playing":
                for e in self.__enemies:  e.draw(screen)
                for p in self.__powerups: p.draw(screen)
                self.__player.draw(screen)
                self.draw_hud()
            elif self.__state == "game_over":
                for e in self.__enemies:  e.draw(screen)
                for p in self.__powerups: p.draw(screen)
                self.__player.draw(screen)
                self.draw_hud()
                self.draw_game_over()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()