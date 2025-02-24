import pygame
import random
import math
from enum import Enum, auto

#Player movement and shooting mechanics

#Various enemy types with different behaviors

#Upgrades system with offensive, defensive, and utility buffs

#Boss enemy with multiple attack phases

#Experience and level progression system

#Collision detection and game-over handling 

pygame.init()

# Constants
screen = pygame.display.set_mode()
SCREEN_WIDTH,SCREEN_HEIGHT = screen.get_size()
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 125, 125)


class UpgradeType(Enum):
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    UTILITY = "utility"


class BossState(Enum):
    PHASE1 = auto()
    PHASE2 = auto()
    PHASE3 = auto()


class Upgrade:
    def __init__(self, name, description, upgrade_type, effect_function):
        self.name = name
        self.description = description
        self.type = upgrade_type
        self.effect = effect_function
        self.level = 0


class Bullet:
    def __init__(self, x, y, target_x, target_y, speed=10, color=GREEN,
                 homing=False, piercing=False, burst=False, damage=10.0, lifespan=-1, max_pierce=2):
        self.x = x
        self.y = y
        self.radius = 5
        self.speed = speed
        self.color = color
        self.homing = homing
        self.piercing = piercing
        self.burst = burst
        self.enemies_hit = 0
        self.max_pierce = max_pierce
        self.ricochet_count = 0
        self.temporal_decay = False
        self.damage = damage
        self.lifespan = lifespan  # Lifespan in frames
        self.age = 0  # Age in frames

        angle = math.atan2(target_y - y, target_x - x)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

    def move(self, enemies=None):
        if self.homing and enemies:
            closest_dist = float('inf')
            closest_enemy = None

            for enemy in enemies:
                dist = math.sqrt((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = enemy

            if closest_enemy:
                angle = math.atan2(closest_enemy.y - self.y, closest_enemy.x - self.x)
                target_dx = math.cos(angle) * self.speed
                target_dy = math.sin(angle) * self.speed

                # Gradual homing
                self.dx = self.dx * 0.9 + target_dx * 0.1
                self.dy = self.dy * 0.9 + target_dy * 0.1

                # Normalize speed
                speed = math.sqrt(self.dx ** 2 + self.dy ** 2)
                self.dx = self.dx / speed * self.speed
                self.dy = self.dy / speed * self.speed

        self.x += self.dx
        self.y += self.dy

        self.age += 1  # Increment age each frame

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def is_off_screen(self):
        return (self.x < 0 or self.x > SCREEN_WIDTH or
                self.y < 0 or self.y > SCREEN_HEIGHT)

    def is_expired(self):
        return self.age >= self.lifespan  # Check if the bullet has exceeded its lifespan


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.color = GREEN
        self.bullets = []
        self.shoot_cooldown = 0
        self.base_shoot_delay = 10
        self.shoot_delay = self.base_shoot_delay
        self.score = 0
        self.experience = 0
        self.level = 1
        # Leveling Formula Parameters
        self.base_xp = 100  # Base XP required for level 1
        self.growth_rate = 0.05  # Growth rate of XP required per level
        self.exp_to_level = self.calculate_xp_required(self.level)
        self.angle = 0  # Angle for rotation
        self.sprite = pygame.image.load("Sprites/player.png")  # Load player sprite
        self.base_damage = 10.0

        # Upgrade flags
        self.upgrades = []
        self.burst_fire_level = 0
        self.burst_fire_counter = -1
        self.shield_cooldown = 0
        self.piercing_level = 0
        self.shield_active = False
        self.has_energy_shield = False
        self.has_nanobot_repair = False
        self.homing_rounds = False
        self.piercing_shots = False
        self.ricochet_rounds = False
        self.temporal_decay = False
        self.damage_multiplier = 1.0

    def add_upgrade(self, upgrade):
        self.upgrades.append(upgrade)
        upgrade.effect(self)

    def move(self, keys):
        if keys[pygame.K_w] and self.y - self.speed > 0:
            self.y -= self.speed
        if keys[pygame.K_s] and self.y + self.speed < SCREEN_HEIGHT:
            self.y += self.speed
        if keys[pygame.K_a] and self.x - self.speed > 0:
            self.x -= self.speed
        if keys[pygame.K_d] and self.x + self.speed < SCREEN_WIDTH:
            self.x += self.speed

    def auto_shoot(self, mouse_x, mouse_y):
        if self.shoot_cooldown <= 0:
            if self.burst_fire_counter == 2:  # Every third shot
                spread_count = 3 + (2 * (self.burst_fire_level-1))  # 3, 5, 7 bullets based on level
                spread_angle = 30 + (10 * self.burst_fire_level)  # Wider spread with each level

                half_spread = spread_angle / 2
                if spread_count > 1:
                    step = spread_angle / (spread_count - 1)
                    angles = [half_spread - (step * i) for i in range(spread_count)]
                else:
                    angles = [0]

                for angle in angles:
                    rad_angle = math.radians(angle)
                    dx = mouse_x - self.x
                    dy = mouse_y - self.y
                    rotated_dx = dx * math.cos(rad_angle) - dy * math.sin(rad_angle)
                    rotated_dy = dx * math.sin(rad_angle) + dy * math.cos(rad_angle)
                    target_x = self.x + rotated_dx
                    target_y = self.y + rotated_dy
                    bullet = Bullet(self.x, self.y, target_x, target_y,
                                    homing=self.homing_rounds,
                                    piercing=True if self.piercing_level > 0 else False,
                                    max_pierce=2 + (2 * self.piercing_level),
                                    damage=self.base_damage * self.damage_multiplier)  # Apply damage
                    self.bullets.append(bullet)
                self.burst_fire_counter = 0
            else:
                bullet = Bullet(self.x, self.y, mouse_x, mouse_y,
                                homing=self.homing_rounds,
                                piercing=self.piercing_shots,
                                damage=self.base_damage * self.damage_multiplier)  # Apply damage
                self.bullets.append(bullet)
                if self.burst_fire_counter != -1:
                    self.burst_fire_counter += 1

            self.shoot_cooldown = self.shoot_delay

    def calculate_xp_required(self, level):
        """Calculates the XP required for a given level."""
        base = self.base_xp
        e = math.e
        growth_rate = self.growth_rate

        # Fix: Handle level 0 and negative levels
        if level <= 0:
            return 0  # Or some other appropriate value

        xp_req = base * pow(e, growth_rate * math.log(level, e))
        return int(xp_req)

    def level_up(self):
        """Handles the leveling up process."""
        self.level += 1
        self.exp_to_level = self.calculate_xp_required(self.level)
        self.experience = 0  # Reset experience after leveling up
        self.max_health += 10  # Example: Increase max health
        self.health = self.max_health  # Restore health
        print(f"Leveled up to level {self.level}!")  # Debug message
        return True

    def update(self, enemies):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.has_nanobot_repair and self.health < self.max_health:
            self.health = min(self.max_health, self.health + 0.1)

        if self.has_energy_shield:
            if self.shield_cooldown > 0:
                self.shield_cooldown -= 1
            elif not self.shield_active:
                self.shield_active = True

        for bullet in self.bullets[:]:
            bullet.move(enemies)
            if bullet.is_off_screen():
                if bullet in self.bullets:
                    self.bullets.remove(bullet)

        # Calculate angle towards the mouse cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))  # Invert dy for correct rotation

    def draw(self, screen):
        # Rotate the sprite
        rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
        sprite_rect = rotated_sprite.get_rect(center=(self.x, self.y))  # Center the sprite

        # Draw the rotated sprite
        screen.blit(rotated_sprite, sprite_rect.topleft)

        # Draw health bar
        pygame.draw.rect(screen, RED, (self.x - 25, self.y - 30, 50, 5))
        pygame.draw.rect(screen, GREEN, (self.x - 25, self.y - 30, 50 * (self.health / self.max_health), 5))

        # Draw shield if active
        if self.shield_active:
            pygame.draw.circle(screen, CYAN, (self.x, self.y), self.radius + 5, 2)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)

        # Draw experience bar at the bottom of the screen
        exp_bar_width = 200
        exp_bar_height = 20
        exp_progress = self.experience / self.exp_to_level
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - exp_bar_width // 2,
                                         SCREEN_HEIGHT - 30, exp_bar_width, exp_bar_height), 2)
        pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH // 2 - exp_bar_width // 2,
                                        SCREEN_HEIGHT - 30,
                                        exp_bar_width * exp_progress, exp_bar_height))


class UpgradeMenu:
    def __init__(self, screen):
        self.screen = screen
        self.options = []
        self.selected_index = 0
        self.font = pygame.font.Font(None, 32)
        self.visible = False

        # Define all possible upgrades
        self.all_upgrades = [
            Upgrade("Burst Fire", "Every third shot fires bullets in a spread pattern",
                    UpgradeType.OFFENSIVE, lambda player: self.upgrade_burst_fire(player)),
            Upgrade("Homing Rounds", "Bullets slightly track nearest enemy",
                    UpgradeType.OFFENSIVE, lambda player: setattr(player, 'homing_rounds', True)),
            Upgrade("Piercing Shots", "Bullets pierce through enemies",
                    UpgradeType.OFFENSIVE, lambda player: self.upgrade_piercing(player)),
            Upgrade("Rate Overdrive", "25% faster fire rate",
                    UpgradeType.OFFENSIVE, lambda player: self.increase_fire_rate(player)),
            Upgrade("Enhanced Damage", "Increase bullet damage by 25%",
                    UpgradeType.OFFENSIVE, lambda player: self.increase_damage(player)),
            Upgrade("Energy Shield", "Absorb one hit every 10 seconds",
                    UpgradeType.DEFENSIVE, lambda player: self.add_shield(player)),
            Upgrade("Nanobot Repair", "Slowly regenerate health",
                    UpgradeType.DEFENSIVE, lambda player: setattr(player, 'has_nanobot_repair', True)),
            Upgrade("Temporal Decay", "Bullets slow enemies briefly",
                    UpgradeType.OFFENSIVE, lambda player: setattr(player, 'temporal_decay', True)),
            Upgrade("I AM SPEED", "Increase speed by 20%",
                    UpgradeType.UTILITY, lambda player: self.increase_speed(player)),
            Upgrade("League Of Tanks", "Increase health by 20%",
                    UpgradeType.UTILITY, lambda player: self.increase_health(player))
        ]

    def upgrade_burst_fire(self, player):
        player.burst_fire_level += 1
        if player.burst_fire_counter == -1:
            player.burst_fire_counter = 0

    def upgrade_piercing(self, player):
        player.piercing_level += 1

    def increase_fire_rate(self, player):
        player.shoot_delay *= 0.75

    def increase_health(self, player):
        player.max_health *= 1.2  # Increase max_health by 20%
        player.health *= 1.2  # Increase health by 20%

    def increase_speed(self, player):
        player.speed *= 1.2  # Increase speed by 20%

    def increase_damage(self, player):
        player.damage_multiplier *= 1.25  # Increase damage by 25%

    def add_shield(self, player):
        player.has_energy_shield = True
        player.shield_active = True
        player.shield_cooldown = 0

    def show(self):
        self.visible = True
        self.options = random.sample(self.all_upgrades, min(3, len(self.all_upgrades)))
        self.selected_index = 0
        pygame.event.clear()  # Clear existing events

    def hide(self):
        self.visible = False

    def draw(self):
        if not self.visible:
            return

        # Draw semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(128)
        s.fill(BLACK)
        self.screen.blit(s, (0, 0))

        # Draw upgrade options
        for i, upgrade in enumerate(self.options):
            color = YELLOW if i == self.selected_index else WHITE
            text = f"{upgrade.name}: {upgrade.description}"
            text_surface = self.font.render(text, True, color)
            x = SCREEN_WIDTH // 2 - text_surface.get_width() // 2
            y = SCREEN_HEIGHT // 2 - len(self.options) * 30 + i * 60
            self.screen.blit(text_surface, (x, y))

    def handle_input(self, event, player):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                selected_upgrade = self.options[self.selected_index]
                player.add_upgrade(selected_upgrade)
                self.hide()
                return True
        return False


class Enemy:
    def __init__(self, x, y, enemy_type, wave=1):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.bullets = []
        self.slowed = False
        self.slow_timer = 0
        self.sprites = {
            "tank": pygame.image.load("Sprites/tank.png"),
            "assassin": pygame.image.load("Sprites/assassin.png"),
            "mage": pygame.image.load("Sprites/mage.png")
        }

        # Scale the tank and mage sprites
        self.sprites["tank"] = pygame.transform.scale(self.sprites["tank"],
                                                      (self.sprites["tank"].get_width() * 3,
                                                       self.sprites["tank"].get_height() * 3))
        self.sprites["mage"] = pygame.transform.scale(self.sprites["mage"],
                                                      (self.sprites["mage"].get_width() * 2,
                                                       self.sprites["mage"].get_height() * 2))

        self.sprite = self.sprites[enemy_type]
        self.angle = 90
        wave_scale = 1 + (wave - 1) * 0.25

        # Set attributes based on enemy type
        if enemy_type == "tank":
            self.radius = 25
            self.base_speed = 2
            self.speed = self.base_speed
            self.health = int(50 * wave_scale)
            self.color = ORANGE
            self.exp_value = 15
        elif enemy_type == "assassin":
            self.radius = 12
            self.base_speed = 4
            self.speed = self.base_speed
            self.health = int(5 * wave_scale)
            self.color = RED
            self.dash_distance = 200
            self.dash_cooldown = 0
            self.dash_delay = 60
            self.is_dashing = False
            self.exp_value = 10
        else:  # mage
            self.radius = 15
            self.base_speed = 2
            self.speed = self.base_speed
            self.health = int(20 * wave_scale)
            self.color = PURPLE
            self.spell_cooldown = 0
            self.spell_delay = 120
            self.exp_value = 20

    def move_towards_player(self, player, enemies):
        if self.slowed:
            if self.slow_timer > 0:
                self.slow_timer -= 1
            else:
                self.slowed = False
                self.speed = self.base_speed

        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance != 0:
            dx = dx / distance
            dy = dy / distance

            # Calculate angle for rotation
            self.angle = math.degrees(math.atan2(-dy, dx))  # Invert dy for correct rotation

            if self.enemy_type == "assassin":
                if distance < self.dash_distance and self.dash_cooldown <= 0:
                    self.is_dashing = True
                    self.dash_cooldown = self.dash_delay
                    self.speed = 15  # Dash speed
                elif self.dash_cooldown <= 0:
                    self.speed = self.base_speed

                if self.dash_cooldown > 0:
                    self.dash_cooldown -= 1

            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed

            # Check collision with other enemies
            can_move = True
            for enemy in enemies:
                if enemy != self:
                    dist = math.sqrt((new_x - enemy.x) ** 2 + (new_y - enemy.y) ** 2)
                    if dist < (self.radius + enemy.radius):
                        can_move = False
                        break

            if can_move:
                self.x = new_x
                self.y = new_y

    def cast_spell(self, player):
        if self.enemy_type == "mage" and self.spell_cooldown <= 0:
            for _ in range(3):
                bullet = Bullet(self.x, self.y, player.x, player.y,
                                speed=4, color=YELLOW, homing=True)
                self.bullets.append(bullet)
            self.spell_cooldown = self.spell_delay

    def update(self, player):
        if self.enemy_type == "mage":
            if self.spell_cooldown > 0:
                self.spell_cooldown -= 1

            for bullet in self.bullets[:]:
                bullet.move([player])  # Pass player as a list for homing
                if bullet.is_off_screen():
                    self.bullets.remove(bullet)

    def draw(self, screen):
        # Rotate the sprite
        rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
        sprite_rect = rotated_sprite.get_rect(center=(self.x, self.y))  # Center the sprite

        # Draw the rotated sprite
        screen.blit(rotated_sprite, sprite_rect.topleft)

        # Draw enemy health bar
        health_width = 30
        max_health = 50 if self.enemy_type == "tank" else 20 if self.enemy_type == "mage" else 5
        if self.enemy_type == "tank":
            pygame.draw.rect(screen, RED, (self.x - health_width / 2, self.y - 50, health_width, 3))
            pygame.draw.rect(screen, GREEN, (self.x - health_width / 2, self.y - 50,
                                             health_width * (self.health / max_health), 3))
        else:
            pygame.draw.rect(screen, RED, (self.x - health_width / 2, self.y - 25, health_width, 3))
            pygame.draw.rect(screen, GREEN, (self.x - health_width / 2, self.y - 25,
                                             health_width * (self.health / max_health), 3))

        if self.enemy_type == "mage":
            for bullet in self.bullets:
                bullet.draw(screen)

    def apply_slow(self, duration=60):  # 60 frames = 1 second at 60 FPS
        self.slowed = True
        self.speed = self.base_speed * 0.5  # 50% slow
        self.slow_timer = duration


# Add Boss class
class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "tank")
        self.radius = 40
        self.base_speed = 3
        self.speed = self.base_speed
        self.health = 100000
        self.max_health = 100000
        self.color = RED
        self.exp_value = 500
        self.state = BossState.PHASE1
        self.attack_cooldown = 0
        self.attack_delay = 60
        self.movement_timer = 0
        self.target_x = SCREEN_WIDTH // 2
        self.target_y = SCREEN_HEIGHT // 4  # Boss stays in top quarter of screen
        self.sprite = pygame.transform.scale(
            pygame.image.load("Sprites/Boss.png"),  # You can replace with a boss sprite
            (120, 120)
        )
        self.bullets = []
        self.angle = 90

    def move_towards_player(self, player, enemies):
        # Override the parent's movement method to ignore the player
        self.movement_timer += 1

        # Change position every 3 seconds (180 frames)
        if self.movement_timer >= 180:
            self.movement_timer = 0
            # Pick a random position in the top quarter of the screen
            self.target_x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
            self.target_y = random.randint(self.radius, SCREEN_HEIGHT // 4)

        # Move towards target position
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 5:  # Only move if we're not very close to target
            dx = dx / distance
            dy = dy / distance
            self.x += dx * self.speed
            self.y += dy * self.speed

        # Update angle for sprite rotation
        self.angle = math.degrees(math.atan2(-dy, dx))

    def special_attack(self, player):
        if self.attack_cooldown <= 0:
            if self.state == BossState.PHASE1:
                # Circle of bullets
                time_factor = pygame.time.get_ticks()/600
                for i in range(-5, 6):
                    x_offset = math.sin(time_factor + i * 0.5) * 100  # Sine wave offset
                    bullet_x = self.x + x_offset  # Modify spawn position
                    bullet_y = self.y  # Start from boss's Y position

                    bullet = Bullet(bullet_x, bullet_y, player.x, player.y,
                                    speed=6, color=PINK, lifespan=300)
                    self.bullets.append(bullet)

            elif self.state == BossState.PHASE2:
                # Triple shot with spread
                angles = [-15, 0, 15]
                for angle in angles:
                    rad_angle = math.radians(angle)
                    dx = player.x - self.x
                    dy = player.y - self.y
                    rotated_dx = dx * math.cos(rad_angle) - dy * math.sin(rad_angle)
                    rotated_dy = dx * math.sin(rad_angle) + dy * math.cos(rad_angle)
                    target_x = self.x + rotated_dx
                    target_y = self.y + rotated_dy
                    bullet = Bullet(self.x, self.y, target_x, target_y,
                                    speed=6, color=RED, homing=False, lifespan=1200)
                    self.bullets.append(bullet)

            elif self.state == BossState.PHASE3:
                # Desperate attack - bullet hell
                for angle in range(0, 360, 20):
                    rad = math.radians(angle)
                    target_x = self.x + math.cos(rad) * 100
                    target_y = self.y + math.sin(rad) * 100
                    bullet = Bullet(self.x, self.y, target_x, target_y,
                                    speed=8, color=YELLOW, homing=False, lifespan=1200)
                    self.bullets.append(bullet)

            self.attack_cooldown = self.attack_delay

    def update(self, player):
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Update state based on health percentage
        health_percent = self.health / self.max_health
        if health_percent <= 0.3:
            self.state = BossState.PHASE3
            self.attack_delay = 45
        elif health_percent <= 0.6:
            self.state = BossState.PHASE2
            self.attack_delay = 50

        # Special attack
        self.special_attack(player)

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.move([player])  # Pass player as a list for homing
            if bullet.is_off_screen() or bullet.is_expired():
                self.bullets.remove(bullet)

    def draw(self, screen):
        # Draw boss sprite
        rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
        sprite_rect = rotated_sprite.get_rect(center=(self.x, self.y))
        screen.blit(rotated_sprite, sprite_rect.topleft)

        # Draw boss health bar at top of screen
        bar_width = SCREEN_WIDTH * 0.8
        bar_height = 20
        x = (SCREEN_WIDTH - bar_width) / 2
        y = 20
        pygame.draw.rect(screen, RED, (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (x, y, bar_width * (self.health / self.max_health), bar_height))

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode()
        pygame.display.set_caption("Bullet Hell Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 60
        self.upgrade_menu = UpgradeMenu(self.screen)
        self.game_over = False
        self.wave = 1
        self.wave_timer = 0
        self.wave_duration = 1800  # 30 seconds at 60 FPS
        self.background = pygame.image.load(
            "BackGround/Background.png").convert()
        self.background = pygame.transform.scale(self.background,self.screen.get_size())
        self.boss = None
        self.victory = False

        self.background_music = None
        self.boss_music = None
        self.victory_music = None
        self.game_over_music = None
        self.music_volume = 0.5
        self.load_music()

    def load_music(self):
        try:
            # Load different music tracks
            pygame.mixer.music.load("Music/background_music.mp3")  # Main background music
            self.boss_music = pygame.mixer.Sound("Music/boss_music.mp3")
            self.victory_music = pygame.mixer.Sound("Music/victory_music.mp3")
            self.game_over_music = pygame.mixer.Sound("Music/game_over_music.mp3")

            # Set volumes
            pygame.mixer.music.set_volume(self.music_volume)
            self.boss_music.set_volume(self.music_volume)
            self.victory_music.set_volume(self.music_volume)
            self.game_over_music.set_volume(self.music_volume)

            # Start playing background music and loop it
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        except Exception as e:
            print(f"Error loading music: {e}")

    def spawn_enemy(self):
        enemy_type = random.choice(["tank", "assassin", "mage"])
        side = random.randint(0, 3)

        if side == 0:  # Top
            x = random.randint(0, SCREEN_WIDTH)
            y = -50
        elif side == 1:  # Right
            x = SCREEN_WIDTH + 50
            y = random.randint(0, SCREEN_HEIGHT)
        elif side == 2:  # Bottom
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 50
        else:  # Left
            x = -50
            y = random.randint(0, SCREEN_HEIGHT)

        self.enemies.append(Enemy(x, y, enemy_type, self.wave))

    def check_collisions(self):
        # Check regular enemy-player collisions
        for enemy in self.enemies[:]:
            if not isinstance(enemy, Boss):  # Skip boss in collision check
                distance = math.sqrt((enemy.x - self.player.x) ** 2 + (enemy.y - self.player.y) ** 2)
                if distance < (enemy.radius + self.player.radius):
                    if self.player.shield_active:
                        self.player.shield_active = False
                        self.player.shield_cooldown = 600  # 10 seconds at 60 FPS
                        self.enemies.remove(enemy)
                    else:
                        self.enemies.remove(enemy)
                        self.player.health -= 10

        # Check player bullet-enemy collisions (including boss)
        for bullet in self.player.bullets[:]:
            for enemy in self.enemies[:]:
                distance = math.sqrt((enemy.x - bullet.x) ** 2 + (enemy.y - bullet.y) ** 2)
                if distance < (enemy.radius + bullet.radius):
                    if bullet.temporal_decay:
                        enemy.apply_slow()

                    enemy.health -= bullet.damage
                    if enemy.health <= 0:
                        if isinstance(enemy, Boss):
                            self.victory = True
                        self.player.experience += enemy.exp_value
                        self.player.score += enemy.exp_value * 10
                        self.enemies.remove(enemy)

                    if not bullet.piercing or bullet.enemies_hit >= bullet.max_pierce:
                        if bullet in self.player.bullets:
                            self.player.bullets.remove(bullet)
                    else:
                        bullet.enemies_hit += 1
                    break

        # Check mage bullet-player collisions
        for enemy in self.enemies:
            if enemy.enemy_type == "mage" or isinstance(enemy, Boss):
                for bullet in enemy.bullets[:]:
                    distance = math.sqrt((self.player.x - bullet.x) ** 2 + (self.player.y - bullet.y) ** 2)
                    if distance < (self.player.radius + bullet.radius):
                        if self.player.shield_active:
                            self.player.shield_active = False
                            self.player.shield_cooldown = 600
                        else:
                            self.player.health -= 5
                        enemy.bullets.remove(bullet)

    def check_level_up(self):
        if self.player.experience >= self.player.exp_to_level:
            self.player.experience -= self.player.exp_to_level
            self.player.level += 1
            self.player.exp_to_level = int(self.player.exp_to_level * 1.2)
            self.upgrade_menu.show()

    def update_wave(self):
        self.wave_timer += 1
        if self.wave_timer >= self.wave_duration:
            self.wave += 1
            self.wave_timer = 0
            self.enemy_spawn_delay = max(20, int(self.enemy_spawn_delay * 0.9))  # Increase spawn rate
            self.player.health = min(self.player.max_health, self.player.health + 20)  # Heal between waves
            if self.wave == 5:
                pygame.mixer.music.stop()
                self.boss_music.play(-1)
                self.boss = Boss(SCREEN_WIDTH // 2, -100)
                self.enemies.append(self.boss)

    def check_victory(self):
        if self.wave >= 20 and self.boss and self.boss.health <= 0:
            self.victory = True

    def draw_victory(self):
        victory_text = self.font.render("VICTORY!", True, YELLOW)
        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        wave_text = self.font.render(f"Waves Survived: {self.wave}", True, WHITE)
        level_text = self.font.render(f"Final Level: {self.player.level}", True, WHITE)

        text_y = SCREEN_HEIGHT // 2 - 100
        for text in [victory_text, score_text, wave_text, level_text]:
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, text_y))
            self.screen.blit(text, text_rect)
            text_y += 50

        restart_text = self.font.render("Press R to Play Again or ESC to Quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(restart_text, restart_rect)

    def draw_game_over(self):
        game_over_text = self.font.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        wave_text = self.font.render(f"Waves Survived: {self.wave}", True, WHITE)
        level_text = self.font.render(f"Final Level: {self.player.level}", True, WHITE)

        text_y = SCREEN_HEIGHT // 2 - 100
        for text in [game_over_text, score_text, wave_text, level_text]:
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, text_y))
            self.screen.blit(text, text_rect)
            text_y += 50

        restart_text = self.font.render("Press R to Restart or ESC to Quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(restart_text, restart_rect)

    def draw_hud(self):
        # Draw score
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Draw wave information
        wave_text = self.font.render(f"Wave {self.wave}", True, WHITE)
        wave_rect = wave_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        self.screen.blit(wave_text, wave_rect)

        # Draw health
        health_text = self.font.render(f"Health: {int(self.player.health)}", True, WHITE)
        self.screen.blit(health_text, (10, 40))

        # Draw level
        level_text = self.font.render(f"Level: {self.player.level}", True, WHITE)
        level_rect = level_text.get_rect(topright=(SCREEN_WIDTH - 10, 40))
        self.screen.blit(level_text, level_rect)

    def run(self):
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.game_over:
                        # Reset game
                        pygame.mixer.stop()
                        self.__init__()
                        self.game_over = False

                if self.upgrade_menu.handle_input(event, self.player):
                    continue
            if not self.game_over and not self.upgrade_menu.visible and not self.victory:
                # Game logic
                keys = pygame.key.get_pressed()
                self.player.move(keys)

                # Auto-shoot at mouse position
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.player.auto_shoot(mouse_x, mouse_y)

                self.player.update(self.enemies)

                # Enemy spawning and updating
                self.enemy_spawn_timer += 1
                if self.enemy_spawn_timer >= self.enemy_spawn_delay:
                    self.spawn_enemy()
                    self.enemy_spawn_timer = 0

                # Update wave
                self.update_wave()

                # Update enemies
                for enemy in self.enemies:
                    enemy.move_towards_player(self.player, self.enemies)
                    enemy.update(self.player)
                    if enemy.enemy_type == "mage":
                        enemy.cast_spell(self.player)

                self.check_collisions()
                self.check_level_up()

                if self.player.health <= 0:
                    self.game_over = True
                self.check_victory()

            # Drawing
            self.screen.fill(BLACK)

            if self.victory:
                self.draw_victory()
                pygame.mixer.music.stop()
                self.victory_music.play()
            elif not self.game_over:
                self.screen.blit(self.background, (0, 0))
                self.player.draw(self.screen)
                for enemy in self.enemies:
                    enemy.draw(self.screen)
                self.draw_hud()
                self.upgrade_menu.draw()
            else:
                self.draw_game_over()
                pygame.mixer.music.stop()
                self.game_over_music.play(-1)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
