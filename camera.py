import pygame as pg
from settings import WIDTH, HEIGHT

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.camera = pg.Rect(0, 0, width, height)
        print(f"Camera initialized with dimensions {width}x{height}")
    
    def apply(self, pos):
        """Apply camera offset to a position vector"""
        # Return the position adjusted for camera position
        return pos.x - self.x, pos.y - self.y
    
    def apply_rect(self, rect):
        """Apply camera offset to a rectangle"""
        return pg.Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)
    
    def update(self, target):
        """Update camera position to center on a target"""
        # Calculate new camera position to center on target
        self.x = target.pos.x - WIDTH // 2
        self.y = target.pos.y - HEIGHT // 2
        
        # Update the camera rect
        self.camera = pg.Rect(self.x, self.y, self.width, self.height)
        
        # Keep camera within world bounds
        self.x = max(0, min(self.x, self.width - WIDTH))
        self.y = max(0, min(self.y, self.height - HEIGHT))
    
    def update_for_two_players(self, player1, player2):
        """Update camera to keep both players in view"""
        # Find the midpoint between the two players
        mid_x = (player1.pos.x + player2.pos.x) / 2
        mid_y = (player1.pos.y + player2.pos.y) / 2
        
        # Set camera position to center on midpoint
        self.x = mid_x - WIDTH // 2
        self.y = mid_y - HEIGHT // 2
        
        # Update the camera rect
        self.camera = pg.Rect(self.x, self.y, self.width, self.height)
        
        # Keep camera within world bounds
        self.x = max(0, min(self.x, self.width - WIDTH))
        self.y = max(0, min(self.y, self.height - HEIGHT))
        
        # Debug info
        if pg.time.get_ticks() % 1000 < 10:  # Print only occasionally
            print(f"Camera at {self.x}, {self.y}, tracking midpoint {mid_x}, {mid_y}")
