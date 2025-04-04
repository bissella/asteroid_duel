import os
import random

import pygame as pg

from camera import Camera
from settings import (
    ASSET_FOLDER,
    ASTEROID_COUNT,
    BLACK,
    BLUE,
    FPS,
    FULLSCREEN,
    GREEN,
    HEIGHT,
    PLAYER1_CONTROLS,
    PLAYER1_START,
    PLAYER2_CONTROLS,
    PLAYER2_START,
    PLAYER_RESPAWN_SAFE_DISTANCE,
    POWERUP_COLORS,
    POWERUP_SPAWN_CHANCE,
    POWERUP_TYPES,
    RED,
    TITLE,
    WHITE,
    WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
    YELLOW,
)
from sprites import Asteroid, Explosion, MotherShip, Player, PowerUp

# pylint: disable=no-member


class Game:
    def __init__(self):
        # Initialize pygame and create window
        pg.init()
        
        # Set up the display based on settings
        if FULLSCREEN:
            self.screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
            print("Game running in fullscreen mode")
        else:
            self.screen = pg.display.set_mode((WIDTH, HEIGHT))
            print(f"Game running in windowed mode: {WIDTH}x{HEIGHT}")
            
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.playing = False
        self.dt = 0.0
        self.asset_folder = os.path.join(
            os.path.dirname(__file__), ASSET_FOLDER
        )  # pylint: disable=no-member

        # Initialize sprite groups in __init__ to address pylint warnings
        self.all_sprites = None
        self.players = None
        self.asteroids = None
        self.lasers = None
        self.lasers_p1 = None
        self.lasers_p2 = None
        self.enemies = None
        self.motherships = None
        self.powerups = None  # New group for powerups
        self.player1 = None
        self.player2 = None
        self.camera = None

        # Game score
        self.score = 0

        # Mothership spawn timer
        self.last_mothership_spawn = 0

        # Asteroid respawn timer and settings
        self.last_asteroid_spawn = 0
        self.asteroid_spawn_delay = (
            5000  # Initial delay between asteroid spawns (5 seconds)
        )
        self.min_asteroid_spawn_delay = 2000  # Minimum delay (2 seconds)
        self.asteroid_spawn_rate_decrease = (
            -10
        )  # Decrease spawn delay by this amount each spawn
        self.max_asteroids = 30  # Maximum number of asteroids allowed at once

        # Initialize font
        self.font_name = pg.font.match_font("arial")

        self.load_assets()

    def load_assets(self):
        # No assets to load - using primitive shapes
        pass

    def new(self):
        # Start a new game
        self.score = 0

        # Create sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.players = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.lasers = pg.sprite.Group()
        self.lasers_p1 = pg.sprite.Group()
        self.lasers_p2 = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.motherships = pg.sprite.Group()
        self.powerups = pg.sprite.Group()  # Initialize powerups group

        # Create player objects - use the controls from settings.py
        self.player1 = Player(self, PLAYER1_START, PLAYER1_CONTROLS, GREEN, 1)
        self.player2 = Player(self, PLAYER2_START, PLAYER2_CONTROLS, RED, 2)

        # Create asteroids
        for _ in range(ASTEROID_COUNT):
            Asteroid(self)

        # Initialize mothership spawn timer
        self.last_mothership_spawn = pg.time.get_ticks()

        # Spawn initial mothership
        MotherShip(self)

        # Create camera
        self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)

        # Start the game
        self.playing = True
        print("Game initialized with players and asteroids")

    def run(self):
        # Print debug info
        print("Game started. Players and asteroids initialized.")
        print(
            f"Player 1 position: {self.player1.pos}, Player 2 position: {self.player2.pos}"
        )
        print(f"Number of asteroids: {len(self.asteroids)}")

        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000  # Convert to seconds
            self.events()
            self.update()
            self.draw()

            # Add debug info
            if pg.time.get_ticks() % 1000 < 20:  # Print every ~1 second
                print(f"FPS: {self.clock.get_fps():.1f}")
                print(
                    f"Player 1 pos: {self.player1.pos}, Player 2 pos: {self.player2.pos}"
                )
                print(f"Camera pos: {self.camera.x:.0f}, {self.camera.y:.0f}")

    def update(self):
        # Game loop - update
        self.all_sprites.update(self.dt)

        # Check for collisions between lasers and asteroids
        for laser in self.lasers:
            # Check collision with asteroids
            hits = pg.sprite.spritecollide(laser, self.asteroids, False)
            for hit in hits:
                laser.kill()
                hit.kill()
                Explosion(self, hit.pos, hit.size)

                # Chance to spawn a powerup from destroyed asteroid
                if random.random() < POWERUP_SPAWN_CHANCE["asteroid"]:
                    # Create powerup at asteroid position with a slight offset for visibility
                    powerup_pos = hit.pos + pg.math.Vector2(
                        random.uniform(-10, 10), random.uniform(-10, 10)
                    )
                    PowerUp(self, powerup_pos)
                    print(f"PowerUp spawned at {powerup_pos} from asteroid")

                # Spawn smaller asteroids
                if hit.size > 20:
                    for _ in range(2):
                        Asteroid(self, hit.pos, hit.size // 2)
                # Increase score
                self.score += 10
                break

            # Check collision with enemy ships
            hits = pg.sprite.spritecollide(laser, self.enemies, False)
            for hit in hits:
                laser.kill()
                if isinstance(hit, MotherShip):
                    hit.take_damage(10)  # Mothership takes less damage
                else:
                    hit.take_damage(30)  # Regular enemy ships take full damage
                break

            # Check collision with players (can't hit yourself)
            # Players are now immune to each other's weapons
            if laser in self.lasers_p1:
                if pg.sprite.collide_rect(laser, self.player2) and self.player2.alive():
                    laser.kill()
                    # No damage applied - players are immune to each other
                    print("Laser from Player 1 passed through Player 2")
                    # self.player2.health -= 10
                    # if self.player2.health <= 0:
                    #     self.player2.kill()
                    #     Explosion(self, self.player2.pos, self.player2.size)
            elif laser in self.lasers_p2:
                if pg.sprite.collide_rect(laser, self.player1) and self.player1.alive():
                    laser.kill()
                    # No damage applied - players are immune to each other
                    print("Laser from Player 2 passed through Player 1")
                    # self.player1.health -= 10
                    # if self.player1.health <= 0:
                    #     self.player1.kill()
                    #     Explosion(self, self.player1.pos, self.player1.size)

        # Check for collisions between players and asteroids
        for player in self.players:
            if not player.alive():
                continue

            hits = pg.sprite.spritecollide(player, self.asteroids, True)
            for hit in hits:
                player.health -= 20
                Explosion(self, hit.pos, hit.size)
                if player.health <= 0:
                    player.kill()
                    Explosion(self, player.pos, player.size)

        # Check for collisions between players and enemy ships
        for player in self.players:
            if not player.alive():
                continue

            hits = pg.sprite.spritecollide(player, self.enemies, False)
            for hit in hits:
                if isinstance(hit, MotherShip):
                    # Check if player has an active shield
                    if player.active_powerups["shield"]:
                        print(f"Player {player.player_num}'s shield protected from mothership collision!")
                        # Shield protects from damage but is removed after mothership collision
                        player.active_powerups["shield"] = False
                        player.shield_health = 0
                        # Create shield break effect
                        for _ in range(5):
                            Explosion(self, player.pos, random.randint(10, 20))
                    else:
                        # No shield, player takes damage
                        player.health -= 30
                    
                    # Player collision still damages mothership
                    hit.take_damage(50)
                else:
                    # For regular enemy ships
                    if player.active_powerups["shield"]:
                        # Shield absorbs damage from regular enemies
                        player.shield_health -= 10
                        print(f"Player {player.player_num}'s shield absorbed enemy collision. Shield health: {player.shield_health}")
                        
                        # If shield is depleted, remove it
                        if player.shield_health <= 0:
                            player.active_powerups["shield"] = False
                            print(f"Player {player.player_num}'s shield depleted from enemy collision")
                    else:
                        # No shield, player takes damage
                        player.health -= 10
                    
                    # Enemy ship destroyed on player collision
                    hit.take_damage(100)

                if player.health <= 0:
                    player.kill()
                    Explosion(self, player.pos, player.size)

        # Check for collisions between asteroids and enemy ships
        for enemy in self.enemies:
            hits = pg.sprite.spritecollide(enemy, self.asteroids, True)
            for hit in hits:
                Explosion(self, hit.pos, hit.size)
                if isinstance(enemy, MotherShip):
                    enemy.take_damage(20)  # Mothership takes less damage from asteroids
                else:
                    enemy.take_damage(
                        100
                    )  # Regular enemy ships are destroyed by asteroids

        # Spawn new asteroids over time
        self.handle_asteroid_spawning()

        # Check for mothership spawn
        now = pg.time.get_ticks()
        if now - self.last_mothership_spawn > 10000:
            self.last_mothership_spawn = now
            if random.random() < 0.1 and len(self.motherships) < 1:
                MotherShip(self)
                print("Mothership spawned")

        # Update camera position
        if self.player1.alive() and self.player2.alive():
            # If both players are alive, center camera between them
            self.camera.update_for_two_players(self.player1, self.player2)
        elif self.player1.alive():
            # If only player 1 is alive, follow them
            self.camera.update(self.player1)
        elif self.player2.alive():
            # If only player 2 is alive, follow them
            self.camera.update(self.player2)
        else:
            # If both players are dead, follow a random sprite if any exist
            if len(self.all_sprites) > 0:
                # Convert to list to use random.choice
                sprites = list(self.all_sprites)
                if sprites:
                    self.camera.update(random.choice(sprites))

        # Check for game over condition
        if not self.player1.alive() and not self.player2.alive():
            self.playing = False
            print("Game over - both players destroyed")

    def handle_asteroid_spawning(self):
        """Spawn new asteroids at random intervals"""
        now = pg.time.get_ticks()

        # Only spawn if we're below the maximum number of asteroids
        if len(self.asteroids) < 10:
            # Check if it's time to spawn a new asteroid
            if now - self.last_asteroid_spawn > 2000:
                self.last_asteroid_spawn = now

                # Create a new asteroid at a random position away from players
                self.spawn_asteroid_away_from_players()

                print(f"Asteroid spawned. Current count: {len(self.asteroids)}")

    def spawn_asteroid_away_from_players(self):
        """Spawn an asteroid at a random position, but not too close to players"""
        min_distance = 200  # Minimum distance from players
        max_attempts = 10  # Maximum attempts to find a suitable position

        for _ in range(max_attempts):
            # Generate random position within world bounds
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            pos = pg.math.Vector2(x, y)

            # Check distance from players
            safe_distance = True
            for player in self.players:
                if player.alive() and player.pos.distance_to(pos) < min_distance:
                    safe_distance = False
                    break

            # If position is safe, create asteroid and return
            if safe_distance:
                size = random.randint(20, 50)
                Asteroid(self, pos, size)
                return

        # If we couldn't find a safe position after max attempts, just spawn it randomly
        x = random.randint(0, WORLD_WIDTH)
        y = random.randint(0, WORLD_HEIGHT)
        pos = pg.math.Vector2(x, y)
        size = random.randint(20, 50)
        Asteroid(self, pos, size)

    def mothership_destroyed(self):
        """Called when a mothership is destroyed. Respawns dead players and increases score."""
        # Increase score
        self.score += 100

        print("Mothership destroyed! Checking for dead players to respawn...")

        # Spawn a powerup at the mothership's position
        # Always spawn a powerup when a mothership is destroyed
        if hasattr(self, "last_mothership_pos"):
            # Make the powerup more visible by increasing its size
            powerup_type = random.choice(POWERUP_TYPES)
            PowerUp(self, self.last_mothership_pos, powerup_type)
            print(
                f"PowerUp {powerup_type} spawned at mothership position {self.last_mothership_pos}"
            )

        # Find a safe spawn position away from the mothership's last position
        safe_spawn_pos = self.find_safe_spawn_position()

        # Respawn player 1 if dead
        if not self.player1.alive():
            print("Respawning Player 1")
            # Create a new player at the safe position with a small random offset
            spawn_pos = pg.math.Vector2(
                safe_spawn_pos.x + random.randint(-50, 50),
                safe_spawn_pos.y + random.randint(-50, 50),
            )
            self.player1 = Player(self, spawn_pos, PLAYER1_CONTROLS, GREEN, 1)
            print("Copying powerups from Player 2 to Player 1")
            self.player1.copy_powerups_from(self.player2)

            # Create a respawn effect
            for _ in range(3):
                Explosion(self, spawn_pos, random.randint(20, 40))

        # Respawn player 2 if dead
        if not self.player2.alive():
            print("Respawning Player 2")
            # Create a new player at the safe position with a small random offset
            spawn_pos = pg.math.Vector2(
                safe_spawn_pos.x + random.randint(-50, 50),
                safe_spawn_pos.y + random.randint(-50, 50),
            )
            self.player2 = Player(self, spawn_pos, PLAYER2_CONTROLS, RED, 2)
            print("Copying powerups from Player 1 to Player 2")
            self.player2.copy_powerups_from(self.player1)

            # Create a respawn effect
            for _ in range(3):
                Explosion(self, spawn_pos, random.randint(20, 40))

    def find_safe_spawn_position(self):
        """
        Find a safe position to respawn players within the viewable area but away from enemies.
        Will attempt multiple times to find a suitable position.
        """
        # Get the current camera view boundaries
        if self.player1.alive() and self.player2.alive():
            # If both players are alive, center is between them
            center_x = (self.player1.pos.x + self.player2.pos.x) / 2
            center_y = (self.player1.pos.y + self.player2.pos.y) / 2
        elif self.player1.alive():
            # If only player 1 is alive, center on them
            center_x = self.player1.pos.x
            center_y = self.player1.pos.y
        elif self.player2.alive():
            # If only player 2 is alive, center on them
            center_x = self.player2.pos.x
            center_y = self.player2.pos.y
        else:
            # Default to center of the world if no players alive
            center_x = WORLD_WIDTH / 2
            center_y = WORLD_HEIGHT / 2
        
        # Calculate the current viewable area boundaries
        view_left = max(0, center_x - WIDTH / 2)
        view_right = min(WORLD_WIDTH, center_x + WIDTH / 2)
        view_top = max(0, center_y - HEIGHT / 2)
        view_bottom = min(WORLD_HEIGHT, center_y + HEIGHT / 2)
        
        # Try to find a safe position within the viewable area
        max_attempts = 50  # Maximum number of attempts to find a safe position
        for attempt in range(max_attempts):
            # Generate a random position within the viewable area
            x = random.uniform(view_left + 50, view_right - 50)
            y = random.uniform(view_top + 50, view_bottom - 50)
            test_pos = pg.math.Vector2(x, y)
            
            # Check if this position is safe (away from motherships and enemies)
            is_safe = True
            
            # Check distance from motherships
            for mothership in self.motherships:
                if test_pos.distance_to(mothership.pos) < PLAYER_RESPAWN_SAFE_DISTANCE:
                    is_safe = False
                    break
            
            # Check distance from enemy ships
            if is_safe:
                for enemy in self.enemies:
                    if test_pos.distance_to(enemy.pos) < PLAYER_RESPAWN_SAFE_DISTANCE:
                        is_safe = False
                        break
            
            # Check distance from asteroids
            if is_safe:
                for asteroid in self.asteroids:
                    if test_pos.distance_to(asteroid.pos) < PLAYER_RESPAWN_SAFE_DISTANCE / 2:  # Less strict for asteroids
                        is_safe = False
                        break
            
            # If we found a safe position, return it
            if is_safe:
                print(f"Found safe spawn position at {test_pos} on attempt {attempt+1}")
                return test_pos
        
        # If we couldn't find a safe position after max attempts, use the center of the viewable area
        print(f"Could not find safe spawn position after {max_attempts} attempts, using center of view")
        return pg.math.Vector2((view_left + view_right) / 2, (view_top + view_bottom) / 2)

    def events(self):
        # Game Loop - Events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            # Player shooting is now handled in the Player class update

    def draw(self):
        # Game loop - render
        self.screen.fill(BLACK)

        # Draw grid for reference
        self.draw_grid()

        # Apply camera offset to all sprites
        for sprite in self.all_sprites:
            # Special handling for players to draw ghost ships when near boundaries
            if isinstance(sprite, Player):
                sprite.draw(self.screen)
            else:
                self.screen.blit(sprite.image, sprite.rect)

        # Calculate UI positions based on screen size
        margin = int(WIDTH * 0.01)  # 1% of screen width as margin
        health_bar_width = int(WIDTH * 0.1)  # 10% of screen width
        
        # Draw player health bars
        if self.player1.alive():
            self.draw_health_bar(self.screen, margin, margin, self.player1.health, health_bar_width)
        if self.player2.alive():
            self.draw_health_bar(self.screen, WIDTH - margin - health_bar_width, margin, self.player2.health, health_bar_width)

        # Draw player powerup indicators
        if self.player1.alive():
            # Draw powerup indicators for player 1
            y_offset = margin + 30
            powerup_x = margin + health_bar_width // 2
            if self.player1.active_powerups["shotgun"]:
                self.draw_text("SHOTGUN", 20, POWERUP_COLORS["shotgun"], powerup_x, y_offset)
                y_offset += 25
            if self.player1.active_powerups["laser_stream"]:
                self.draw_text(
                    "LASER STREAM", 20, POWERUP_COLORS["laser_stream"], powerup_x, y_offset
                )
                y_offset += 25
            if self.player1.active_powerups["shield"]:
                self.draw_text(
                    f"SHIELD: {self.player1.shield_health}",
                    20,
                    POWERUP_COLORS["shield"],
                    powerup_x,
                    y_offset,
                )

        if self.player2.alive():
            # Draw powerup indicators for player 2
            y_offset = margin + 30
            powerup_x = WIDTH - margin - health_bar_width // 2
            if self.player2.active_powerups["shotgun"]:
                self.draw_text(
                    "SHOTGUN", 20, POWERUP_COLORS["shotgun"], powerup_x, y_offset, align="right"
                )
                y_offset += 25
            if self.player2.active_powerups["laser_stream"]:
                self.draw_text(
                    "LASER STREAM",
                    20,
                    POWERUP_COLORS["laser_stream"],
                    powerup_x,
                    y_offset,
                    align="right"
                )
                y_offset += 25
            if self.player2.active_powerups["shield"]:
                self.draw_text(
                    f"SHIELD: {self.player2.shield_health}",
                    20,
                    POWERUP_COLORS["shield"],
                    powerup_x,
                    y_offset,
                    align="right"
                )

        # Draw score
        self.draw_text(
            f"Score: {self.score}", 30, WHITE, WIDTH // 2, margin, align="center"
        )

        # Draw FPS
        self.draw_text(
            f"FPS: {int(self.clock.get_fps())}",
            20,
            WHITE,
            WIDTH - margin,
            HEIGHT - margin,
            align="right",
        )

        # Update display
        pg.display.flip()

    def draw_grid(self):
        # Draw a grid to help visualize the world (debug)
        grid_size = 100
        for x in range(0, WORLD_WIDTH, grid_size):
            x_screen = x - self.camera.camera.x
            if 0 <= x_screen < WIDTH:
                pg.draw.line(
                    self.screen, (20, 20, 20), (x_screen, 0), (x_screen, HEIGHT)
                )
        for y in range(0, WORLD_HEIGHT, grid_size):
            y_screen = y - self.camera.camera.y
            if 0 <= y_screen < HEIGHT:
                pg.draw.line(
                    self.screen, (20, 20, 20), (0, y_screen), (WIDTH, y_screen)
                )

    def draw_health_bar(self, screen, x, y, health, width):
        """Draw a health bar at the specified position"""
        BAR_HEIGHT = 10
        fill = (health / 100) * width
        outline_rect = pg.Rect(x, y, width, BAR_HEIGHT)
        fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
        pg.draw.rect(screen, RED, fill_rect)
        pg.draw.rect(screen, WHITE, outline_rect, 2)

    def quit(self):
        pg.quit()  # pylint: disable=no-member

    def draw_text(self, text, size, color, x, y, align="center"):
        """Helper method to draw text on screen"""
        font = pg.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "center":
            text_rect.midtop = (x, y)
        elif align == "left":
            text_rect.topleft = (x, y)
        elif align == "right":
            text_rect.topright = (x, y)
        self.screen.blit(text_surface, text_rect)
        return text_rect

    def wait_for_key(self):
        """Wait for a key press to continue"""
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pg.KEYUP:
                    waiting = False

    def show_start_screen(self):
        """Game start screen"""
        # Fill screen with black
        self.screen.fill(BLACK)

        # Draw game title
        self.draw_text(TITLE, 48, WHITE, WIDTH / 2, HEIGHT / 4)

        # Draw instructions
        self.draw_text(
            "Two-Player Space Shooter", 22, WHITE, WIDTH / 2, HEIGHT / 2 - 40
        )
        self.draw_text(
            "Player 1: WASD to move, SPACE to shoot", 22, RED, WIDTH / 2, HEIGHT / 2
        )
        self.draw_text(
            "Player 2: Arrow keys to move, Right CTRL to shoot",
            22,
            BLUE,
            WIDTH / 2,
            HEIGHT / 2 + 30,
        )

        # Draw a pulsing "Press any key" message
        pulse = (pg.time.get_ticks() % 1000) / 1000  # Value between 0 and 1
        pulse_color = [int(c * (0.5 + 0.5 * pulse)) for c in YELLOW]
        self.draw_text(
            "Press any key to begin", 22, pulse_color, WIDTH / 2, HEIGHT * 3 / 4
        )

        # Draw sample ships
        # Player 1 ship (red triangle)
        ship_size = 30
        p1_ship = pg.Surface((ship_size, ship_size), pg.SRCALPHA)
        points = [(ship_size // 2, 0), (0, ship_size), (ship_size, ship_size)]
        pg.draw.polygon(p1_ship, RED, points)
        self.screen.blit(p1_ship, (WIDTH // 4 - ship_size // 2, HEIGHT * 3 / 5))

        # Player 2 ship (blue triangle)
        p2_ship = pg.Surface((ship_size, ship_size), pg.SRCALPHA)
        pg.draw.polygon(p2_ship, BLUE, points)
        self.screen.blit(p2_ship, (WIDTH * 3 // 4 - ship_size // 2, HEIGHT * 3 / 5))

        # Draw sample asteroid
        asteroid_size = 40
        asteroid = pg.Surface((asteroid_size, asteroid_size), pg.SRCALPHA)
        pg.draw.circle(
            asteroid,
            (139, 69, 19),
            (asteroid_size // 2, asteroid_size // 2),
            asteroid_size // 2,
        )
        # Add some grey craters
        for _ in range(3):
            crater_size = asteroid_size // 8
            crater_pos = (
                random.randint(crater_size, asteroid_size - crater_size),
                random.randint(crater_size, asteroid_size - crater_size),
            )
            pg.draw.circle(asteroid, (128, 128, 128), crater_pos, crater_size)
        self.screen.blit(asteroid, (WIDTH // 2 - asteroid_size // 2, HEIGHT * 3 / 5))

        # Update the display
        pg.display.flip()

        # Print debug info
        print("Start screen displayed. Waiting for key press...")

        # Wait for a key press to start
        self.wait_for_key()
        print("Key pressed. Starting game...")

    def show_go_screen(self):
        """Game over screen"""
        if not self.running:
            return

        # Fill screen with black
        self.screen.fill(BLACK)

        # Draw game over text
        self.draw_text("GAME OVER", 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text(
            "Press any key to play again", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4
        )

        # Update the display
        pg.display.flip()

        # Wait for a key press to restart
        self.wait_for_key()


# Create the game object
g = Game()
# Show the start screen
g.show_start_screen()

# Game loop
while g.running:
    # Start a new game
    g.new()
    # Run the game loop
    g.run()
    # Show the game over screen
    g.show_go_screen()

# Quit the game
g.quit()
