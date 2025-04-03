import os
import pygame as pg
from settings import (
    WIDTH, HEIGHT, TITLE, FPS, WORLD_WIDTH, WORLD_HEIGHT,
    BLACK, ASSET_FOLDER, PLAYER1_START, PLAYER2_START,
    PLAYER1_CONTROLS, PLAYER2_CONTROLS, RED, BLUE, ASTEROID_COUNT,
    WHITE, YELLOW, BROWN, GREY
)
from sprites import Player, Asteroid, Explosion
from camera import Camera
import random

# pylint: disable=no-member


class Game:
    def __init__(self):
        # Initialize pygame and create window
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))  # pylint: disable=no-member
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.playing = False
        self.dt = 0.0
        self.asset_folder = os.path.join(os.path.dirname(__file__), ASSET_FOLDER)  # pylint: disable=no-member
        
        # Initialize sprite groups in __init__ to address pylint warnings
        self.all_sprites = None
        self.players = None
        self.asteroids = None
        self.lasers = None
        self.lasers_p1 = None
        self.lasers_p2 = None
        self.player1 = None
        self.player2 = None
        self.camera = None
        
        # Initialize font
        self.font_name = pg.font.match_font('arial')
        
        self.load_assets()

    def load_assets(self):
        # No assets to load - using primitive shapes
        pass

    def new(self):
        # Initialize game variables
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.players = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.lasers = pg.sprite.Group()
        self.lasers_p1 = pg.sprite.Group()
        self.lasers_p2 = pg.sprite.Group()
        
        # Create the camera - use WIDTH and HEIGHT instead of WORLD dimensions
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Create players
        self.player1 = Player(self, PLAYER1_START, PLAYER1_CONTROLS, RED, 1)
        self.player2 = Player(self, PLAYER2_START, PLAYER2_CONTROLS, BLUE, 2)
        
        # Create asteroids
        for _ in range(ASTEROID_COUNT):
            Asteroid(self)
        
        # Set the camera to follow the midpoint between players
        self.camera.update_for_two_players(self.player1, self.player2)
        
        # Start the game
        self.playing = True
        print("Game initialized with players and asteroids")

    def run(self):
        # Print debug info
        print("Game started. Players and asteroids initialized.")
        print(f"Player 1 position: {self.player1.pos}, Player 2 position: {self.player2.pos}")
        print(f"Number of asteroids: {len(self.asteroids)}")
        
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000  # Convert to seconds
            self.events()
            self.update()
            self.draw()
            
            # Add debug info
            if pg.time.get_ticks() % 1000 < 20:  # Print every ~1 second
                print(f"FPS: {self.clock.get_fps():.1f}")
                print(f"Player 1 pos: {self.player1.pos}, Player 2 pos: {self.player2.pos}")
                print(f"Camera pos: {self.camera.camera.topleft}")

    def update(self):
        # Update all sprites
        self.all_sprites.update(self.dt)
        
        # Update camera to follow both players
        if self.player1.alive() and self.player2.alive():
            self.camera.update_for_two_players(self.player1, self.player2)
        elif self.player1.alive():
            self.camera.update(self.player1)
        elif self.player2.alive():
            self.camera.update(self.player2)
        
        # Collision detection is now handled in the Laser class update method
        
        # Check for game over condition
        if not self.player1.alive() and not self.player2.alive():
            self.playing = False
            print("Game over - both players destroyed")

    def events(self):
        # Game Loop - Events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            # Player shooting is now handled in the Player class update

    def draw(self):
        # Fill the screen with black
        self.screen.fill(BLACK)  # Clear the screen
        
        # Draw grid for debugging (optional)
        self.draw_grid()
        
        # Draw all sprites with camera offset
        for sprite in self.all_sprites:
            # Calculate camera offset position
            offset_pos = sprite.rect.copy()
            offset_pos.center = self.camera.apply(sprite.pos)
            
            # Draw sprite at offset position
            self.screen.blit(sprite.image, offset_pos)
            
            # Draw debug rectangle around sprites
            pg.draw.rect(self.screen, (255, 0, 0), offset_pos, 1)  # Red outline for debugging
        
        # Draw player health bars
        if self.player1.alive():
            self.draw_health_bar(self.screen, 10, 10, self.player1.health)
        if self.player2.alive():
            self.draw_health_bar(self.screen, WIDTH - 110, 10, self.player2.health)
        
        # Draw FPS counter
        self.draw_text(f"FPS: {int(self.clock.get_fps())}", 22, WHITE, WIDTH - 60, HEIGHT - 30)
        
        # Draw player positions for debugging
        self.draw_text(f"P1: {self.player1.pos.x:.0f}, {self.player1.pos.y:.0f}", 16, WHITE, 10, HEIGHT - 50)
        self.draw_text(f"P2: {self.player2.pos.x:.0f}, {self.player2.pos.y:.0f}", 16, WHITE, 10, HEIGHT - 30)
        self.draw_text(f"Camera: {self.camera.x:.0f}, {self.camera.y:.0f}", 16, WHITE, 10, HEIGHT - 70)
        
        # Update the display
        pg.display.flip()

    def draw_grid(self):
        # Draw a grid to help visualize the world (debug)
        grid_size = 100
        for x in range(0, WORLD_WIDTH, grid_size):
            x_screen = x - self.camera.camera.x
            if 0 <= x_screen < WIDTH:
                pg.draw.line(self.screen, (20, 20, 20), (x_screen, 0), (x_screen, HEIGHT))
        for y in range(0, WORLD_HEIGHT, grid_size):
            y_screen = y - self.camera.camera.y
            if 0 <= y_screen < HEIGHT:
                pg.draw.line(self.screen, (20, 20, 20), (0, y_screen), (WIDTH, y_screen))

    def draw_health_bar(self, screen, x, y, health):
        """Draw a health bar at the specified position"""
        BAR_WIDTH = 100
        BAR_HEIGHT = 10
        fill = (health / 100) * BAR_WIDTH
        outline_rect = pg.Rect(x, y, BAR_WIDTH, BAR_HEIGHT)
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
        self.draw_text("Two-Player Space Shooter", 22, WHITE, WIDTH / 2, HEIGHT / 2 - 40)
        self.draw_text("Player 1: WASD to move, SPACE to shoot", 22, RED, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Player 2: Arrow keys to move, Right CTRL to shoot", 22, BLUE, WIDTH / 2, HEIGHT / 2 + 30)
        
        # Draw a pulsing "Press any key" message
        pulse = (pg.time.get_ticks() % 1000) / 1000  # Value between 0 and 1
        pulse_color = [int(c * (0.5 + 0.5 * pulse)) for c in YELLOW]
        self.draw_text("Press any key to begin", 22, pulse_color, WIDTH / 2, HEIGHT * 3 / 4)
        
        # Draw sample ships
        # Player 1 ship (red triangle)
        ship_size = 30
        p1_ship = pg.Surface((ship_size, ship_size), pg.SRCALPHA)
        points = [(ship_size//2, 0), (0, ship_size), (ship_size, ship_size)]
        pg.draw.polygon(p1_ship, RED, points)
        self.screen.blit(p1_ship, (WIDTH // 4 - ship_size // 2, HEIGHT * 3 / 5))
        
        # Player 2 ship (blue triangle)
        p2_ship = pg.Surface((ship_size, ship_size), pg.SRCALPHA)
        pg.draw.polygon(p2_ship, BLUE, points)
        self.screen.blit(p2_ship, (WIDTH * 3 // 4 - ship_size // 2, HEIGHT * 3 / 5))
        
        # Draw sample asteroid
        asteroid_size = 40
        asteroid = pg.Surface((asteroid_size, asteroid_size), pg.SRCALPHA)
        pg.draw.circle(asteroid, BROWN, (asteroid_size//2, asteroid_size//2), asteroid_size//2)
        # Add some grey craters
        for _ in range(3):
            crater_size = asteroid_size // 8
            crater_pos = (random.randint(crater_size, asteroid_size-crater_size), 
                         random.randint(crater_size, asteroid_size-crater_size))
            pg.draw.circle(asteroid, GREY, crater_pos, crater_size)
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
        self.draw_text("Press any key to play again", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        
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