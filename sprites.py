import pygame as pg
import math
import random
from settings import (
    PLAYER_ACC, PLAYER_FRICTION, PLAYER_ROT_SPEED, PLAYER_SIZE,
    PLAYER_SHOOT_DELAY, PLAYER_DECELERATION,
    LASER_SPEED,
    EXPLOSION_DURATION,
    WIDTH, HEIGHT,
    RED, GREEN, WHITE,
    MOTHERSHIP_SIZE, MOTHERSHIP_HEALTH, MOTHERSHIP_COLOR, MOTHERSHIP_ACC, MOTHERSHIP_FRICTION,
    ENEMY_SHIP_SIZE, ENEMY_SHIP_HEALTH, ENEMY_COLOR, ENEMY_SHIP_ACC, ENEMY_SHIP_FRICTION, ENEMY_MAX_SPEED, ENEMY_SWARM_DISTANCE, ENEMY_SHIP_SPAWN_RATE
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
            (0, self.size),       # Bottom left
            (self.size, self.size) # Bottom right
        ]
        pg.draw.polygon(self.original_image, self.color, points)
        
        # Add a white outline to make the player more visible
        pg.draw.polygon(self.original_image, WHITE, points, 1)
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        
        # Set initial position and movement variables
        self.pos = vec(pos)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.rect.center = self.pos
        self.rot = 0
        self.health = 100
        self.last_shot = 0
        
        # Debug information
        print(f"Player {player_num} initialized at position {self.pos}")
    
    def update(self, dt):
        self.acc = vec(0, 0)
        keys = pg.key.get_pressed()
        
        # Handle rotation
        if keys[self.player_controls['left']]:
            self.rot = (self.rot + PLAYER_ROT_SPEED * dt) % 360
        if keys[self.player_controls['right']]:
            self.rot = (self.rot - PLAYER_ROT_SPEED * dt) % 360
        
        # Update image based on rotation
        self.image = pg.transform.rotate(self.original_image, self.rot)
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center
        
        # Check if player is trying to move in the opposite direction
        moving_forward = keys[self.player_controls['up']]
        moving_backward = keys[self.player_controls['down']]
        
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
            self.acc = direction * (PLAYER_ACC/2)
        
        # Apply quick deceleration when changing directions
        if (moving_forward and self.vel.length() > 0 and self.vel.normalize().dot(vec(0, -1).rotate(-self.rot)) < 0) or \
           (moving_backward and self.vel.length() > 0 and self.vel.normalize().dot(vec(0, 1).rotate(-self.rot)) < 0):
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
        
        # Wrap around screen edges
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH
        if self.pos.y > HEIGHT:
            self.pos.y = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT
        
        # Update rect position to match the new position
        self.rect.center = self.pos
        
        # Handle shooting
        if keys[self.player_controls['fire']]:
            now = pg.time.get_ticks()
            if now - self.last_shot > PLAYER_SHOOT_DELAY:
                self.last_shot = now
                Laser(self.game, self.pos, self.rot, self.color, self)
        
        # Check for collisions with asteroids
        asteroid_hits = pg.sprite.spritecollide(self, self.game.asteroids, False)
        if asteroid_hits:
            for asteroid in asteroid_hits:
                self.take_damage(10)
                # Bounce the asteroid away
                bounce_dir = (self.pos - asteroid.pos).normalize() * -100
                asteroid.vel = bounce_dir
                print(f"Player {self.player_num} collided with asteroid")
                
        # Debug info occasionally
        if pg.time.get_ticks() % 1000 < 10:  # Print only occasionally
            print(f"Player {self.player_num} at {self.pos}, vel: {self.vel}")
    
    def take_damage(self, amount):
        """Reduce player health and handle destruction if health <= 0"""
        self.health -= amount
        print(f"Player {self.player_num} took {amount} damage, health: {self.health}")
        if self.health <= 0:
            self.kill()
            print(f"Player {self.player_num} destroyed!")


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
        offset = vec(0, -player.size/2).rotate(-direction)  # Offset to the front of the ship
        self.pos = vec(pos) + offset
        self.rect.center = self.pos
        
        # Set velocity in the same direction as the ship is pointing
        self.vel = vec(0, -LASER_SPEED).rotate(-direction)
        self.spawn_time = pg.time.get_ticks()
        
        # Debug info
        print(f"Laser fired from player {player.player_num} at {self.pos} with direction {direction}")
    
    def update(self, dt):
        # Update position
        self.pos += self.vel * dt
        self.rect.center = self.pos
        
        # Check if laser is off screen or has existed for too long
        if (self.pos.x < 0 or self.pos.x > WIDTH or 
            self.pos.y < 0 or self.pos.y > HEIGHT or
            pg.time.get_ticks() - self.spawn_time > 2000):
            self.kill()
            return
        
        # Check for collisions with asteroids
        asteroid_hits = pg.sprite.spritecollide(self, self.game.asteroids, True)
        if asteroid_hits:
            self.kill()
            for hit in asteroid_hits:
                print(f"Laser hit asteroid at {hit.pos}")
                # Spawn new asteroid to replace the destroyed one
                Asteroid(self.game)
        
        # Check for collisions with players (only if not the player who fired)
        for player in self.game.players:
            if player != self.player:  # Don't hit the player who fired
                if self.rect.colliderect(player.rect):
                    player.take_damage(20)
                    print(f"Player {player.player_num} hit by laser from Player {self.player.player_num}")
                    self.kill()
                    break


class Explosion(pg.sprite.Sprite):
    def __init__(self, game, center, size=30):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.game.all_sprites.add(self)
        self.pos = vec(center)  # Add position vector for camera tracking
        
        # Create a circular explosion
        self.image = pg.Surface((size, size), flags=SRCALPHA)  # Using SRCALPHA for transparency
        # Draw expanding circles
        pg.draw.circle(self.image, RED, (size//2, size//2), size//2)
        pg.draw.circle(self.image, GREEN, (size//2, size//2), size//3)
        
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
    def __init__(self, game, pos=None):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.size = random.randint(20, 50)
        
        # Create a circular asteroid
        self.original_image = pg.Surface((self.size, self.size), flags=SRCALPHA)
        pg.draw.circle(self.original_image, (150, 150, 150), (self.size // 2, self.size // 2), self.size // 2)
        
        # Add some details to make it look more like an asteroid
        for _ in range(4):
            offset = random.randint(3, self.size // 4)
            angle = random.randint(0, 360)
            x = self.size // 2 + offset * math.cos(math.radians(angle))
            y = self.size // 2 + offset * math.sin(math.radians(angle))
            radius = random.randint(2, self.size // 5)
            pg.draw.circle(self.original_image, (100, 100, 100), (int(x), int(y)), radius)
        
        # Add a white outline to make the asteroid more visible
        pg.draw.circle(self.original_image, WHITE, (self.size // 2, self.size // 2), self.size // 2, 1)
        
        self.image = self.original_image
        self.rect = self.image.get_rect()
        
        # Set position and velocity
        if pos:
            self.pos = vec(pos)
        else:
            # Spawn within the visible area instead of the whole world
            self.pos = vec(
                random.randint(50, WIDTH - 50),
                random.randint(50, HEIGHT - 50)
            )
        
        self.rect.center = self.pos
        
        # Set random velocity
        self.vel = vec(random.uniform(-100, 100), random.uniform(-100, 100))
        
        # Add to sprite groups
        self.game.all_sprites.add(self)
        self.game.asteroids.add(self)
        
        # Debug info
        print(f"Asteroid created at position [{self.pos.x:.0f}, {self.pos.y:.0f}] with velocity [{self.vel.x:.4f}, {self.vel.y:.4f}]")
    
    def update(self, dt):
        # Update position based on velocity
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
        
        # Update rect position
        self.rect.center = self.pos


class MotherShip(pg.sprite.Sprite):
    def __init__(self, game, pos=None):
        self._layer = 2
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.size = MOTHERSHIP_SIZE
        self.health = MOTHERSHIP_HEALTH
        
        # Create a hexagonal mothership
        self.original_image = pg.Surface((self.size, self.size), flags=SRCALPHA)
        # Draw a hexagon
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            x = self.size // 2 + int(self.size // 2 * 0.8 * math.cos(angle))
            y = self.size // 2 + int(self.size // 2 * 0.8 * math.sin(angle))
            points.append((x, y))
        pg.draw.polygon(self.original_image, MOTHERSHIP_COLOR, points)
        
        # Add some details to make it look more like a mothership
        center = (self.size // 2, self.size // 2)
        pg.draw.circle(self.original_image, (200, 200, 200), center, self.size // 4)
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        
        # Set random position if not provided
        if pos is None:
            # Place the mothership at a random edge of the world
            edge = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
            if edge == 0:  # top
                self.pos = vec(random.randint(0, WIDTH), 0)
            elif edge == 1:  # right
                self.pos = vec(WIDTH, random.randint(0, HEIGHT))
            elif edge == 2:  # bottom
                self.pos = vec(random.randint(0, WIDTH), HEIGHT)
            else:  # left
                self.pos = vec(0, random.randint(0, HEIGHT))
        else:
            self.pos = vec(pos)
            
        self.rect.center = self.pos
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.rot = 0
        
        # Spawn timer for enemy ships
        self.last_spawn = pg.time.get_ticks()
        
        # Add to sprite groups
        self.game.all_sprites.add(self)
        self.game.enemies.add(self)
        self.game.motherships.add(self)
    
    def update(self, dt):
        # Slow random movement
        self.acc = vec(random.uniform(-1, 1), random.uniform(-1, 1))
        self.acc = self.acc.normalize() * MOTHERSHIP_ACC
        
        # Apply friction
        self.acc += self.vel * MOTHERSHIP_FRICTION
        
        # Update velocity and position
        self.vel += self.acc * dt
        
        # Limit maximum velocity
        if self.vel.length() > 100:
            self.vel.scale_to_length(100)
            
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
        
        # Spawn enemy ships periodically
        now = pg.time.get_ticks()
        if now - self.last_spawn > ENEMY_SHIP_SPAWN_RATE:
            self.last_spawn = now
            EnemyShip(self.game, self.pos)
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            # Create a large explosion
            Explosion(self.game, self.pos, self.size)
            self.kill()
            
            # Add score
            self.game.score += 100


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
            (0, self.size),       # Bottom left
            (self.size, self.size) # Bottom right
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
        closest_dist = float('inf')
        
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
