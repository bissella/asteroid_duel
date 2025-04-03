import pygame as pg

# Game options/settings
TITLE = "Asteroid Duel"
WIDTH = 1024  # Game window width
HEIGHT = 768  # Game window height
FPS = 60

# World Size Multiplier (reduced from 10x to 3x for better visibility)
WORLD_MULTIPLIER = 3
WORLD_WIDTH = WIDTH * WORLD_MULTIPLIER
WORLD_HEIGHT = HEIGHT * WORLD_MULTIPLIER

# Define Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREY = (128, 128, 128)
BROWN = (165, 42, 42)

# Font settings
FONT_NAME = "arial"

# Player settings (placeholders for now)
PLAYER_ACC = 200
PLAYER_FRICTION = -0.9  # Higher friction value to slow down faster
PLAYER_DECELERATION = 0.95  # Explicit deceleration factor for quick direction changes
PLAYER_ROT_SPEED = 200
PLAYER_HIT_RECT = pg.Rect(0, 0, 35, 35)  # Example hit rectangle
PLAYER_HEALTH = 100
PLAYER_SIZE = 30  # Example size for primitive shape
PLAYER_SHOOT_DELAY = 250  # milliseconds
PLAYER_IMG_P1 = "playerShip1_blue.png"  # Placeholder asset name
PLAYER_IMG_P2 = "playerShip1_red.png"  # Placeholder asset name

# Player start positions (centered in the world)
PLAYER1_START = (WIDTH // 4, HEIGHT // 2)  # Left side of screen
PLAYER2_START = (WIDTH * 3 // 4, HEIGHT // 2)  # Right side of screen

# Laser settings (placeholders)
LASER_SPEED = 500
LASER_LIFETIME = 1000  # milliseconds
LASER_SIZE = (4, 20)  # Small rectangle for laser primitive
LASER_COLOR_P1 = YELLOW  # Example color for Player 1's lasers
LASER_COLOR_P2 = (255, 100, 0)  # Example color (Orange) for Player 2's lasers
LASER_RATE = 150  # milliseconds between shots initially
LASER_COOLDOWN_INCREASE = 50  # ms added to rate after each shot
LASER_COOLDOWN_RECHARGE = 5  # ms subtracted from rate each frame when not firing
LASER_MAX_COOLDOWN = 1000  # Maximum delay
LASER_IMG = "laserBlue01.png"  # Placeholder

# Asteroid settings
# NUM_ASTEROIDS = 1000
ASTEROID_SIZE_MIN = 20
ASTEROID_SIZE_MAX = 50
ASTEROID_SPEED_MAX = 100
ASTEROID_ROT_SPEED_MAX = 60  # degrees per second
ASTEROID_SPAWN_PADDING = 100  # Min distance from edge or player to spawn
ASTEROID_COUNT = 8  # Initial number of asteroids
ASTEROID_IMG = "meteorBrown_med1.png"  # Placeholder image

# Enemy ship settings
MOTHERSHIP_SIZE = 100
MOTHERSHIP_HEALTH = 500
MOTHERSHIP_ACC = 50  # Less nimble than player ships
MOTHERSHIP_FRICTION = -0.05
MOTHERSHIP_SPAWN_DELAY = 30000  # 30 seconds between mothership spawns
MOTHERSHIP_SPAWN_CHANCE = 0.1  # 30% chance to spawn a mothership when timer expires

ENEMY_SHIP_SIZE = 20
ENEMY_SHIP_HEALTH = 30
ENEMY_SHIP_ACC = 150
ENEMY_SHIP_FRICTION = -0.1
ENEMY_SHIP_DAMAGE = 10
ENEMY_SHIP_SPAWN_RATE = 3000  # Spawn a new enemy every 3 seconds from mothership
ENEMY_SWARM_DISTANCE = 200  # Distance at which enemy ships start swarming players
ENEMY_MAX_SPEED = 200
ENEMY_COLOR = (255, 100, 0)  # Orange
MOTHERSHIP_COLOR = (255, 50, 50)  # Red

# Explosion settings
EXPLOSION_DURATION = 500  # milliseconds for the primitive explosion

# PowerUp settings
POWERUP_SIZE = 20
POWERUP_DURATION = 20000  # 20 seconds for temporary powerups
POWERUP_TYPES = ["health", "shotgun", "laser_stream", "shield"]
POWERUP_COLORS = {
    "health": (0, 255, 0),  # Green
    "shotgun": (255, 165, 0),  # Orange
    "laser_stream": (0, 191, 255),  # Deep Sky Blue
    "shield": (138, 43, 226),  # Blue Violet
}
POWERUP_SPAWN_CHANCE = {
    "asteroid": 1.0,  # 10% chance from asteroid
    "mothership": 1.0,  # 100% chance from mothership
}
POWERUP_LIFETIME = (
    10000  # How long a powerup stays on screen before disappearing (10 seconds)
)
POWERUP_SHOTGUN_SPREAD = 15  # Angle in degrees between shotgun lasers
POWERUP_LASER_STREAM_DELAY = 100  # Delay between laser stream shots in milliseconds
POWERUP_SHIELD_HEALTH = 50  # Additional health provided by shield

# Boundary
BOUNDARY_COLOR = RED
BOUNDARY_THICKNESS = 10

# Asset paths (assuming assets are in 'assets' folder)
ASSET_FOLDER = "assets"  # We might need the absolute path later depending on setup

# Player Controls (pygame keys)
PLAYER1_CONTROLS = {
    "up": pg.K_w,  # pylint: disable=no-member
    "down": pg.K_s,  # pylint: disable=no-member
    "left": pg.K_a,  # pylint: disable=no-member
    "right": pg.K_d,  # pylint: disable=no-member
    "fire": pg.K_SPACE,  # pylint: disable=no-member
}
PLAYER2_CONTROLS = {
    "up": pg.K_UP,  # pylint: disable=no-member
    "down": pg.K_DOWN,  # pylint: disable=no-member
    "left": pg.K_LEFT,  # pylint: disable=no-member
    "right": pg.K_RIGHT,  # pylint: disable=no-member
    "fire": pg.K_RSHIFT,  # pylint: disable=no-member
}
