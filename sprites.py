import math
import random

import pygame as pg

from settings import (
    ENEMY_COLOR,
    ENEMY_MAX_SPEED,
    ENEMY_SHIP_ACC,
    ENEMY_SHIP_FRICTION,
    ENEMY_SHIP_HEALTH,
    ENEMY_SHIP_SIZE,
    ENEMY_SWARM_DISTANCE,
    EXPLOSION_DURATION,
    GREEN,
    HEIGHT,
    LASER_SPEED,
    MOTHERSHIP_ACC,
    MOTHERSHIP_COLOR,
    MOTHERSHIP_FRICTION,
    MOTHERSHIP_HEALTH,
    MOTHERSHIP_SIZE,
    PLAYER_ACC,
    PLAYER_DECELERATION,
    PLAYER_FRICTION,
    PLAYER_ROT_SPEED,
    PLAYER_SHOOT_DELAY,
    PLAYER_SIZE,
    POWERUP_COLORS,
    POWERUP_LASER_STREAM_DELAY,
    POWERUP_SHIELD_HEALTH,
    POWERUP_SHOTGUN_SPREAD,
    POWERUP_SIZE,
    POWERUP_TYPES,
    RED,
    WHITE,
    WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)

# Define constants
vec = pg.math.Vector2
SRCALPHA = 0x00010000  # Define SRCALPHA constant


class Player(pg.sprite.Sprite):
    def __init__(self, game, pos, player_controls, color, player_num=1):
        self._layer = 2
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.player_num = player_num
        self.player_controls = player_controls
        self.color = color
        self.size = PLAYER_SIZE

        # Add player to sprite groups
        game.all_sprites.add(self)
        game.players.add(self)

        # Create a triangular ship
        self.original_image = pg.Surface((self.size, self.size), flags=SRCALPHA)

        # Draw a triangle pointing upward
        points = [
            (self.size // 2, 0),  # Top vertex
            (0, self.size),  # Bottom left
            (self.size, self.size),  # Bottom right
        ]
        pg.draw.polygon(self.original_image, self.color, points)

        # Add a white outline to make the player more visible
        pg.draw.polygon(self.original_image, WHITE, points, 1)

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()

        # Set initial position and movement variables
        self.pos = vec(pos)
        self.true_pos = vec(pos)  # Position for collision detection
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.rect.center = self.pos
        self.rot = 0
        self.health = 100
        self.last_shot = 0

        # Ghost ship for boundary transitions
        self.ghost_active = False
        self.ghost_pos = vec(0, 0)

        # Powerup tracking
        self.active_powerups = {
            "shotgun": False,
            "laser_stream": False,
            "shield": False,
        }
        self.shield_health = 0
        self.last_stream_shot = 0  # For laser stream powerup

        # Debug information
        print(f"Player {player_num} initialized at position {self.pos}")

    def update(self, dt):
        self.acc = vec(0, 0)
        keys = pg.key.get_pressed()

        # Handle rotation
        if keys[self.player_controls["left"]]:
            self.rot = (self.rot + PLAYER_ROT_SPEED * dt) % 360
        if keys[self.player_controls["right"]]:
            self.rot = (self.rot - PLAYER_ROT_SPEED * dt) % 360

        # Update image based on rotation
        self.image = pg.transform.rotate(self.original_image, self.rot)
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

        # Check if player is trying to move in the opposite direction
        moving_forward = keys[self.player_controls["up"]]
        moving_backward = keys[self.player_controls["down"]]

        # Handle forward/backward movement
        if moving_forward:
            # Calculate acceleration based on rotation
            # In Pygame, 0 degrees points up, and rotation increases clockwise
            # We need to use negative rotation because Pygame's rotation is opposite to the math convention
            direction = vec(0, -1).rotate(-self.rot)
            self.acc = direction * PLAYER_ACC
        if moving_backward:
            # Reverse direction
            direction = vec(0, 1).rotate(-self.rot)
            self.acc = direction * (PLAYER_ACC / 2)

        # Apply quick deceleration when changing directions
        if (
            moving_forward
            and self.vel.length() > 0
            and self.vel.normalize().dot(vec(0, -1).rotate(-self.rot)) < 0
        ) or (
            moving_backward
            and self.vel.length() > 0
            and self.vel.normalize().dot(vec(0, 1).rotate(-self.rot)) < 0
        ):
            # If moving against current velocity, apply stronger deceleration
            self.vel *= PLAYER_DECELERATION

        # Apply friction - this slows down the ship when not accelerating
        self.acc += self.vel * PLAYER_FRICTION

        # Update velocity based on acceleration
        self.vel += self.acc * dt

        # Limit maximum velocity
        if self.vel.length() > 300:
            self.vel.scale_to_length(300)

        # Update position based on velocity
        self.pos += self.vel * dt
        self.true_pos = vec(self.pos)  # Store true position before wrapping

        # Handle screen wrapping with a buffer zone for smooth transitions
        buffer = self.size * 1.5  # Buffer size based on player size
        transition_zone = self.size * 3  # Zone where ghost ship appears

        # Reset ghost status
        self.ghost_active = False

        # Check if player is near a boundary and set up ghost ship
        if self.pos.x > WIDTH - transition_zone:
            # Near right edge, show ghost on left
            self.ghost_active = True
            self.ghost_pos = vec(self.pos.x - WIDTH, self.pos.y)
        elif self.pos.x < transition_zone:
            # Near left edge, show ghost on right
            self.ghost_active = True
            self.ghost_pos = vec(self.pos.x + WIDTH, self.pos.y)

        if self.pos.y > HEIGHT - transition_zone:
            # Near bottom edge, show ghost on top
            self.ghost_active = True
            self.ghost_pos = vec(self.pos.x, self.pos.y - HEIGHT)
        elif self.pos.y < transition_zone:
            # Near top edge, show ghost on bottom
            self.ghost_active = True
            self.ghost_pos = vec(self.pos.x, self.pos.y + HEIGHT)

        # Wrap around screen edges with buffer
        if self.pos.x > WIDTH + buffer:
            self.pos.x = -buffer
        elif self.pos.x < -buffer:
            self.pos.x = WIDTH + buffer

        if self.pos.y > HEIGHT + buffer:
            self.pos.y = -buffer
        elif self.pos.y < -buffer:
            self.pos.y = HEIGHT + buffer

        # Update rect position to match the new position
        self.rect.center = self.pos

        # Handle shooting based on powerups
        now = pg.time.get_ticks()
        if keys[self.player_controls["fire"]]:
            # Modified to allow multiple powerups to be active simultaneously
            if self.active_powerups["shotgun"] and self.active_powerups["laser_stream"]:
                # If both powerups are active, fire both with a slight delay between them
                self.fire_shotgun(now)
                # Small delay to prevent exact overlap of sound effects
                self.fire_laser_stream(now + 50)
            elif self.active_powerups["shotgun"]:
                self.fire_shotgun(now)
            elif self.active_powerups["laser_stream"]:
                self.fire_laser_stream(now)
            else:
                self.fire_normal_laser(now)

        # Check for collisions with asteroids
        asteroid_hits = pg.sprite.spritecollide(self, self.game.asteroids, False)
        if asteroid_hits:
            for asteroid in asteroid_hits:
                self.take_damage(10)
                # Bounce the asteroid away
                bounce_dir = (self.pos - asteroid.pos).normalize() * -100
                asteroid.vel = bounce_dir
                print(f"Player {self.player_num} collided with asteroid")

        # Check for powerup collisions
        self.check_powerup_collisions()

        # Debug info occasionally
        if pg.time.get_ticks() % 1000 < 10:  # Print only occasionally
            print(f"Player {self.player_num} at {self.pos}, vel: {self.vel}")

    def draw(self, screen):
        """Draw the player and ghost ship if active"""
        # Draw the main ship
        screen.blit(self.image, self.rect)

        # Draw ghost ship if active
        if self.ghost_active:
            ghost_rect = self.rect.copy()
            ghost_rect.center = self.ghost_pos

            # Draw with reduced alpha to indicate it's a ghost
            ghost_img = self.image.copy()
            ghost_img.set_alpha(150)  # Semi-transparent
            screen.blit(ghost_img, ghost_rect)

        # Draw shield if active
        if self.active_powerups["shield"]:
            shield_radius = self.size * 1.5
            shield_surface = pg.Surface(
                (shield_radius * 2, shield_radius * 2), pg.SRCALPHA
            )

            # Draw shield with transparency based on remaining health
            alpha = min(150, int(150 * (self.shield_health / POWERUP_SHIELD_HEALTH)))
            shield_color = (*POWERUP_COLORS["shield"][:3], alpha)

            pg.draw.circle(
                shield_surface,
                shield_color,
                (shield_radius, shield_radius),
                shield_radius,
            )
            shield_rect = shield_surface.get_rect(center=self.rect.center)
            screen.blit(shield_surface, shield_rect)

    def take_damage(self, amount):
        """Reduce player health and handle destruction if health <= 0"""
        # If shield is active, damage shield first
        if self.active_powerups["shield"] and self.shield_health > 0:
            self.shield_health -= amount
            print(
                f"Player {self.player_num} shield took damage. Shield health: {self.shield_health}"
            )

            # If shield is depleted, remove it
            if self.shield_health <= 0:
                self.active_powerups["shield"] = False
                print(f"Player {self.player_num} shield depleted")
        else:
            # No shield or shield depleted, damage player directly
            self.health -= amount
            print(
                f"Player {self.player_num} took {amount} damage, health: {self.health}"
            )

            # Check if player is destroyed
            if self.health <= 0:
                self.kill()
                print(f"Player {self.player_num} destroyed")
                # Create explosion effect
                Explosion(self.game, self.pos, self.size * 2)

    def fire_normal_laser(self, now):
        """Fire a single laser with normal cooldown"""
        if now - self.last_shot > PLAYER_SHOOT_DELAY:
            self.last_shot = now
            Laser(self.game, self.pos, self.rot, self.color, self)

    def fire_shotgun(self, now):
        """Fire three lasers in a spread pattern"""
        if now - self.last_shot > PLAYER_SHOOT_DELAY:
            self.last_shot = now
            # Center laser
            Laser(self.game, self.pos, self.rot, self.color, self)
            # Left laser
            Laser(
                self.game, self.pos, self.rot + POWERUP_SHOTGUN_SPREAD, self.color, self
            )
            # Right laser
            Laser(
                self.game, self.pos, self.rot - POWERUP_SHOTGUN_SPREAD, self.color, self
            )

    def fire_laser_stream(self, now):
        """Fire a continuous stream of lasers with reduced cooldown"""
        if now - self.last_stream_shot > POWERUP_LASER_STREAM_DELAY:
            self.last_stream_shot = now
            Laser(self.game, self.pos, self.rot, self.color, self)

    def check_powerup_collisions(self):
        """Check if player has collected any powerups"""
        hits = pg.sprite.spritecollide(self, self.game.powerups, True)
        for powerup in hits:
            self.apply_powerup(powerup.type)

    def apply_powerup(self, powerup_type):
        """Apply the effect of a collected powerup"""
        if powerup_type == "health":
            # Restore health to full
            old_health = self.health
            self.health = 100
            print(
                f"Player {self.player_num} health restored from {old_health} to {self.health}"
            )

        elif powerup_type == "shotgun":
            # Enable shotgun mode - no longer disables other weapon powerups
            self.active_powerups["shotgun"] = True
            print(f"Player {self.player_num} activated shotgun powerup")

        elif powerup_type == "laser_stream":
            # Enable laser stream mode - no longer disables other weapon powerups
            self.active_powerups["laser_stream"] = True
            print(f"Player {self.player_num} activated laser stream powerup")

        elif powerup_type == "shield":
            # Add shield or restore shield health
            self.active_powerups["shield"] = True
            self.shield_health = POWERUP_SHIELD_HEALTH
            print(
                f"Player {self.player_num} activated shield powerup. Shield health: {self.shield_health}"
            )


class Laser(pg.sprite.Sprite):
    def __init__(self, game, pos, direction, color, player):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.player = player

        # Add to sprite groups
        game.all_sprites.add(self)
        game.lasers.add(self)

        # Add to the appropriate player's laser group
        if player.player_num == 1:
            self.game.lasers_p1.add(self)
        else:
            self.game.lasers_p2.add(self)

        # Determine laser color based on player color
        self.color = color

        # Create a line for the laser
        self.width, self.height = 10, 4  # Laser dimensions
        self.original_image = pg.Surface((self.width, self.height), flags=SRCALPHA)
        pg.draw.rect(self.original_image, self.color, (0, 0, self.width, self.height))

        # Add a white outline to make the laser more visible
        pg.draw.rect(self.original_image, WHITE, (0, 0, self.width, self.height), 1)

        # Store the direction for movement calculations
        self.direction = direction

        # Rotate the laser to match the ship's direction
        # Need to adjust by 90 degrees because our rectangle is horizontal by default
        self.image = pg.transform.rotate(self.original_image, direction - 90)
        self.rect = self.image.get_rect()

        # Calculate the position at the front of the ship (top vertex of triangle)
        # The ship is a triangle with the top point being the front
        # We need to offset from the center based on rotation
        offset = vec(0, -player.size / 2).rotate(
            -direction
        )  # Offset to the front of the ship
        self.pos = vec(pos) + offset
        self.rect.center = self.pos

        # Set velocity in the same direction as the ship is pointing
        self.vel = vec(0, -LASER_SPEED).rotate(-direction)
        self.spawn_time = pg.time.get_ticks()

        # Debug info
        print(
            f"Laser fired from player {player.player_num} at {self.pos} with direction {direction}"
        )

    def update(self, dt):
        # Update position
        self.pos += self.vel * dt
        self.rect.center = self.pos

        # Check if laser is off screen or has existed for too long
        if (
            self.pos.x < 0
            or self.pos.x > WIDTH
            or self.pos.y < 0
            or self.pos.y > HEIGHT
            or pg.time.get_ticks() - self.spawn_time > 2000
        ):
            self.kill()
            return

        # Check for collisions with asteroids
        asteroid_hits = pg.sprite.spritecollide(self, self.game.asteroids, True)
        if asteroid_hits:
            self.kill()
            for hit in asteroid_hits:
                print(f"Laser hit asteroid at {hit.pos}")
                # Spawn new asteroid to replace the destroyed one
                hit.split()

        # Check for collisions with players (only if not the player who fired)
        for player in self.game.players:
            if player != self.player:  # Don't hit the player who fired
                if self.rect.colliderect(player.rect):
                    player.take_damage(20)
                    print(
                        f"Player {player.player_num} hit by laser from Player {self.player.player_num}"
                    )
                    self.kill()
                    break


class Explosion(pg.sprite.Sprite):
    def __init__(self, game, center, size=30):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.game.all_sprites.add(self)
        self.pos = vec(center)  # Add position vector for camera tracking

        # Create a circular explosion
        self.image = pg.Surface(
            (size, size), flags=SRCALPHA
        )  # Using SRCALPHA for transparency
        # Draw expanding circles
        pg.draw.circle(self.image, RED, (size // 2, size // 2), size // 2)
        pg.draw.circle(self.image, GREEN, (size // 2, size // 2), size // 3)

        self.rect = self.image.get_rect()
        self.rect.center = center
        self.lifetime = 0
        self.max_lifetime = EXPLOSION_DURATION  # Duration in milliseconds

    def update(self, dt):
        self.lifetime += dt * 1000  # Convert to milliseconds
        if self.lifetime >= self.max_lifetime:
            self.kill()
        else:
            # Fade out the explosion over time
            alpha = 255 * (1 - self.lifetime / self.max_lifetime)
            self.image.set_alpha(alpha)


class Asteroid(pg.sprite.Sprite):
    def __init__(self, game, pos=None, size=None):
        pg.sprite.Sprite.__init__(self)
        self.game = game

        # Set size - either provided or random
        if size is None:
            self.size = random.randint(20, 50)
        else:
            self.size = size
            
        # Determine if this is a powerup asteroid (10% chance for new asteroids)
        self.has_powerup = False
        self.powerup_type = None
        if pos is None:  # Only for newly spawned asteroids, not splits
            self.has_powerup = random.random() < 0.1  # 10% chance
            if self.has_powerup:
                self.powerup_type = random.choice(POWERUP_TYPES)

        # Create a circular asteroid
        self.original_image = pg.Surface((self.size, self.size), flags=SRCALPHA)
        pg.draw.circle(
            self.original_image,
            (150, 150, 150),
            (self.size // 2, self.size // 2),
            self.size // 2,
        )

        # Add some details to make it look more like an asteroid
        # Only add details if the asteroid is large enough
        if self.size >= 15:
            detail_count = min(4, max(1, self.size // 10))  # Scale details with size
            for _ in range(detail_count):
                # Ensure we don't get a division by zero or empty range
                max_offset = max(3, self.size // 4)
                offset = random.randint(2, max_offset)
                angle = random.randint(0, 360)
                x = self.size // 2 + offset * math.cos(math.radians(angle))
                y = self.size // 2 + offset * math.sin(math.radians(angle))
                radius = max(1, random.randint(1, self.size // 5))
                pg.draw.circle(
                    self.original_image, (100, 100, 100), (int(x), int(y)), radius
                )
                
        # If it's a powerup asteroid, add a pink center
        if self.has_powerup:
            # Draw a pink center to indicate it contains a powerup
            pg.draw.circle(
                self.original_image,
                (255, 105, 180),  # Hot pink
                (self.size // 2, self.size // 2),
                self.size // 4,  # Center is 1/4 the size of the asteroid
            )

        # Add a white outline to make the asteroid more visible
        pg.draw.circle(
            self.original_image,
            WHITE,
            (self.size // 2, self.size // 2),
            self.size // 2,
            1,
        )

        self.image = self.original_image
        self.rect = self.image.get_rect()

        # Set position and velocity
        if pos:
            self.pos = vec(pos)
        else:
            # Spawn within the visible area instead of the whole world
            self.pos = vec(
                random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
            )

        self.rect.center = self.pos

        # Set random velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(30, 100)
        self.vel = vec(speed * math.cos(angle), speed * math.sin(angle))

        # Add to sprite groups
        self.game.all_sprites.add(self)
        self.game.asteroids.add(self)

        # Debug info
        if not pos:  # Only print for newly spawned asteroids, not splits
            print(
                f"Asteroid created at position {[int(self.pos.x), int(self.pos.y)]} with velocity {[round(self.vel.x, 4), round(self.vel.y, 4)]}"
            )

    def update(self, dt):
        # Update position
        self.pos += self.vel * dt
        self.rect.center = self.pos

        # Wrap around screen edges
        if self.pos.x < -self.size:
            self.pos.x = WIDTH + self.size
        elif self.pos.x > WIDTH + self.size:
            self.pos.x = -self.size
        if self.pos.y < -self.size:
            self.pos.y = HEIGHT + self.size
        elif self.pos.y > HEIGHT + self.size:
            self.pos.y = -self.size

    def split(self):
        """Split the asteroid into two smaller ones if it's large enough"""
        # If this asteroid has a powerup, spawn it instead of splitting
        if self.has_powerup:
            # Create a powerup at the asteroid's position
            PowerUp(self.game, self.pos, self.powerup_type)
            print(f"PowerUp {self.powerup_type} released from asteroid at {self.pos}")
            
            # Create a small explosion
            Explosion(self.game, self.pos, self.size // 2)
            
            # Remove this asteroid
            self.kill()
            return
            
        # Normal asteroid splitting behavior
        if self.size > 15:  # Only split if the asteroid is big enough
            # Create two smaller asteroids
            for _ in range(2):
                # Create a new asteroid at the same position but with a smaller size
                offset = vec(random.randint(-10, 10), random.randint(-10, 10))
                new_pos = self.pos + offset
                new_size = max(10, self.size // 2)  # Ensure minimum size
                Asteroid(self.game, new_pos, new_size)

            # Create a small explosion
            Explosion(self.game, self.pos, self.size // 2)

            # Remove this asteroid
            self.kill()
        else:
            # Too small to split, just remove it
            Explosion(self.game, self.pos, self.size // 2)
            self.kill()


class MotherShip(pg.sprite.Sprite):
    """Large enemy ship that spawns smaller enemy ships"""

    def __init__(self, game, pos=None):
        self._layer = 2
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.size = MOTHERSHIP_SIZE

        # Add to sprite groups
        game.all_sprites.add(self)
        game.enemies.add(self)
        game.motherships.add(self)

        # Create a circular mothership
        self.image = pg.Surface((self.size * 2, self.size * 2), flags=SRCALPHA)
        pg.draw.circle(self.image, MOTHERSHIP_COLOR, (self.size, self.size), self.size)

        # Add details to make it look more like a mothership
        # Draw a smaller circle in the center
        pg.draw.circle(
            self.image, (200, 200, 200), (self.size, self.size), self.size // 2
        )

        # Draw some "windows" around the edge
        for angle in range(0, 360, 45):
            x = self.size + int(math.cos(math.radians(angle)) * (self.size * 0.7))
            y = self.size + int(math.sin(math.radians(angle)) * (self.size * 0.7))
            pg.draw.circle(self.image, (255, 255, 0), (x, y), self.size // 8)

        self.rect = self.image.get_rect()

        # Set initial position and movement variables
        if pos:
            self.pos = vec(pos)
        else:
            # Spawn at a random edge of the screen
            side = random.randint(0, 3)
            if side == 0:  # Top
                self.pos = vec(random.randint(0, WIDTH), -self.size)
            elif side == 1:  # Right
                self.pos = vec(WIDTH + self.size, random.randint(0, HEIGHT))
            elif side == 2:  # Bottom
                self.pos = vec(random.randint(0, WIDTH), HEIGHT + self.size)
            else:  # Left
                self.pos = vec(-self.size, random.randint(0, HEIGHT))

        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.rect.center = self.pos

        # Mothership health
        self.health = MOTHERSHIP_HEALTH

        # Enemy ship spawn timer
        self.last_spawn = pg.time.get_ticks()
        self.spawn_delay = 5000  # 5 seconds between enemy ship spawns

        print(f"Mothership spawned at {self.pos}")

    def update(self, dt):
        # Find the closest player
        target = None
        closest_dist = float("inf")

        for player in self.game.players:
            if player.alive():
                dist = self.pos.distance_to(player.pos)
                if dist < closest_dist:
                    closest_dist = dist
                    target = player

        # Define a radius within which the mothership will follow players
        follow_radius = MOTHERSHIP_SIZE * 15  # Adjust this value as needed

        # If a player is within follow radius, move towards them
        if target and closest_dist < follow_radius:
            # Calculate direction to target
            direction = (target.pos - self.pos).normalize()
            self.acc = direction * MOTHERSHIP_ACC

            # Apply some small randomness to movement
            self.acc += vec(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
        else:
            # Random movement if no target in range
            self.acc = vec(random.uniform(-1, 1), random.uniform(-1, 1))
            if self.acc.length() > 0:
                self.acc = self.acc.normalize() * MOTHERSHIP_ACC

        # Apply friction
        self.acc += self.vel * MOTHERSHIP_FRICTION

        # Update velocity and position
        self.vel += self.acc * dt
        self.pos += self.vel * dt

        # Wrap around screen edges
        if self.pos.x > WIDTH + self.size:
            self.pos.x = -self.size
        if self.pos.x < -self.size:
            self.pos.x = WIDTH + self.size
        if self.pos.y > HEIGHT + self.size:
            self.pos.y = -self.size
        if self.pos.y < -self.size:
            self.pos.y = HEIGHT + self.size

        self.rect.center = self.pos

        # Spawn enemy ships
        now = pg.time.get_ticks()
        if now - self.last_spawn > self.spawn_delay:
            self.last_spawn = now
            EnemyShip(self.game, self.pos)
            print(f"Enemy ship spawned from mothership at {self.pos}")

    def take_damage(self, amount):
        """Reduce mothership health and handle destruction if health <= 0"""
        self.health -= amount
        print(f"Mothership took {amount} damage, health: {self.health}")

        if self.health <= 0:
            # Store position before destroying for powerup spawning
            self.game.last_mothership_pos = vec(self.pos)

            self.kill()
            print("Mothership destroyed!")

            # Create a large explosion
            Explosion(self.game, self.pos, self.size * 2)

            # Notify game that mothership was destroyed
            self.game.mothership_destroyed()

            # Spawn two new motherships when destroyed
            # Only spawn if there aren't too many motherships already
            if (
                len(self.game.motherships) < 3
            ):  # Including this one that's about to be removed
                # Spawn in different positions
                pos1 = vec(
                    self.pos.x + random.randint(-200, 200),
                    self.pos.y + random.randint(-200, 200),
                )
                pos2 = vec(
                    self.pos.x + random.randint(-200, 200),
                    self.pos.y + random.randint(-200, 200),
                )

                # Remove this mothership before spawning new ones
                self.kill()

                # Spawn new motherships
                MotherShip(self.game, pos1)
                MotherShip(self.game, pos2)
            else:
                self.kill()


class EnemyShip(pg.sprite.Sprite):
    def __init__(self, game, pos):
        self._layer = 2
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.size = ENEMY_SHIP_SIZE
        self.health = ENEMY_SHIP_HEALTH

        # Create a triangular enemy ship
        self.original_image = pg.Surface((self.size, self.size), flags=SRCALPHA)
        # Draw a triangle pointing upward
        points = [
            (self.size // 2, 0),  # Top vertex
            (0, self.size),  # Bottom left
            (self.size, self.size),  # Bottom right
        ]
        pg.draw.polygon(self.original_image, ENEMY_COLOR, points)

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.pos = vec(pos)
        self.rect.center = self.pos
        self.vel = vec(random.uniform(-1, 1), random.uniform(-1, 1))
        self.vel = self.vel.normalize() * random.randint(50, 100)
        self.acc = vec(0, 0)
        self.rot = 0

        # Add to sprite groups
        self.game.all_sprites.add(self)
        self.game.enemies.add(self)

    def update(self, dt):
        # Find the closest player
        target = None
        closest_dist = float("inf")

        for player in self.game.players:
            if player.alive():
                dist = self.pos.distance_to(player.pos)
                if dist < closest_dist:
                    closest_dist = dist
                    target = player

        # If a player is within swarm distance, move towards them
        if target and closest_dist < ENEMY_SWARM_DISTANCE:
            # Calculate direction to target
            direction = (target.pos - self.pos).normalize()
            self.acc = direction * ENEMY_SHIP_ACC

            # Update rotation to face the target
            self.rot = math.degrees(math.atan2(-direction.y, direction.x)) - 90
            self.image = pg.transform.rotate(self.original_image, self.rot)
            self.rect = self.image.get_rect()
        else:
            # Random movement if no target in range
            self.acc = vec(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
            self.acc = self.acc.normalize() * (ENEMY_SHIP_ACC / 2)

        # Apply friction
        self.acc += self.vel * ENEMY_SHIP_FRICTION

        # Update velocity and position
        self.vel += self.acc * dt

        # Limit maximum velocity
        if self.vel.length() > ENEMY_MAX_SPEED:
            self.vel.scale_to_length(ENEMY_MAX_SPEED)

        self.pos += self.vel * dt

        # Wrap around screen edges
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH
        if self.pos.y > HEIGHT:
            self.pos.y = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT

        self.rect.center = self.pos

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            # Create an explosion
            Explosion(self.game, self.pos, self.size)
            self.kill()

            # Add score
            self.game.score += 10


class PowerUp(pg.sprite.Sprite):
    """PowerUp class for various player enhancements"""

    def __init__(self, game, pos, powerup_type=None):
        self._layer = 3  # Increased layer to appear above most objects
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.type = powerup_type or random.choice(POWERUP_TYPES)
        self.pos = vec(pos)
        self.vel = vec(
            random.uniform(-20, 20), random.uniform(-20, 20)
        )  # Small random movement
        self.size = int(
            POWERUP_SIZE * 1.5
        )  # Increased size for better visibility, convert to int
        self.color = POWERUP_COLORS[self.type]

        # Create sprite groups
        game.all_sprites.add(self)
        game.powerups.add(self)

        # Create a circular powerup with an icon
        self.image = pg.Surface((self.size * 2, self.size * 2), flags=SRCALPHA)
        pg.draw.circle(self.image, self.color, (self.size, self.size), self.size)

        # Add a white outline
        pg.draw.circle(
            self.image, WHITE, (self.size, self.size), self.size, 3
        )  # Thicker outline

        # Add an icon based on powerup type
        if self.type == "health":
            # Draw a plus sign
            pg.draw.line(
                self.image,
                WHITE,
                (self.size, self.size - self.size // 2),
                (self.size, self.size + self.size // 2),
                4,
            )  # Thicker lines
            pg.draw.line(
                self.image,
                WHITE,
                (self.size - self.size // 2, self.size),
                (self.size + self.size // 2, self.size),
                4,
            )  # Thicker lines
        elif self.type == "shotgun":
            # Draw three lines representing spread shots
            pg.draw.line(
                self.image,
                WHITE,
                (self.size - self.size // 2, self.size),
                (self.size + self.size // 2, self.size),
                3,
            )  # Thicker lines
            pg.draw.line(
                self.image,
                WHITE,
                (self.size - self.size // 2, self.size + self.size // 3),
                (self.size + self.size // 2, self.size - self.size // 3),
                3,
            )  # Thicker lines
            pg.draw.line(
                self.image,
                WHITE,
                (self.size - self.size // 2, self.size - self.size // 3),
                (self.size + self.size // 2, self.size + self.size // 3),
                3,
            )  # Thicker lines
        elif self.type == "laser_stream":
            # Draw multiple short lines representing stream
            for i in range(-self.size // 2, self.size // 2, 4):
                pg.draw.line(
                    self.image,
                    WHITE,
                    (self.size - self.size // 2, self.size + i),
                    (self.size + self.size // 2, self.size + i),
                    3,
                )  # Thicker lines
        elif self.type == "shield":
            # Draw a circle representing shield
            pg.draw.circle(
                self.image, WHITE, (self.size, self.size), self.size // 2, 3
            )  # Thicker lines

        self.rect = self.image.get_rect()
        self.rect.center = self.pos

        # Set spawn time for animation effects
        self.spawn_time = pg.time.get_ticks()

        print(f"PowerUp {self.type} created at {self.pos}")

    def update(self, dt):
        # Move with slight drift
        self.pos += self.vel * dt

        # Apply friction to slow down
        self.vel *= 0.98

        # Wrap around screen edges
        if self.pos.x > WORLD_WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WORLD_WIDTH
        if self.pos.y > WORLD_HEIGHT:
            self.pos.y = 0
        if self.pos.y < 0:
            self.pos.y = WORLD_HEIGHT

        # Update rect position
        self.rect.center = self.pos

        # Make the powerup pulse/rotate for visibility
        # More pronounced pulsing effect
        scale = 0.3 * math.sin(pg.time.get_ticks() * 0.01) + 1.0
        center = self.rect.center
        self.image = pg.transform.rotozoom(self.image, 2, scale)  # Faster rotation
        self.rect = self.image.get_rect()
        self.rect.center = center
