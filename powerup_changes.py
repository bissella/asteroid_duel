"""
This file contains code snippets to implement powerup sharing between players.
Copy these code snippets to the appropriate locations in the game files.
"""

# 1. SPRITES.PY CHANGES

# Add this method to the Player class in sprites.py
def copy_powerups_from(self, other_player):
    """Copy all active powerups from another player"""
    if other_player and other_player.alive():
        # Copy all active powerups
        for powerup_type, active in other_player.active_powerups.items():
            if active:
                self.active_powerups[powerup_type] = True
                print(f"Player {self.player_num} received {powerup_type} powerup from Player {other_player.player_num}")
        
        # Copy shield health if shield is active
        if other_player.active_powerups["shield"]:
            self.shield_health = other_player.shield_health

# Replace the check_powerup_collisions method in the Player class with this:
def check_powerup_collisions(self):
    """Check if player has collected any powerups"""
    hits = pg.sprite.spritecollide(self, self.game.powerups, True)
    for powerup in hits:
        # Apply to self
        self.apply_powerup(powerup.type)
        
        # Share with other player
        other_player = None
        if self.player_num == 1 and self.game.player2.alive():
            other_player = self.game.player2
        elif self.player_num == 2 and self.game.player1.alive():
            other_player = self.game.player1
            
        if other_player:
            other_player.apply_powerup(powerup.type)
            print(f"Powerup {powerup.type} shared with Player {other_player.player_num}")

# 2. MAIN.PY CHANGES

# Modify the player respawn code in the mothership_destroyed method:

# After creating player1, add this code:
# Copy powerups from player 2 if alive
if self.player2.alive():
    print("Copying powerups from Player 2 to Player 1")
    self.player1.copy_powerups_from(self.player2)

# After creating player2, add this code:
# Copy powerups from player 1 if alive
if self.player1.alive():
    print("Copying powerups from Player 1 to Player 2")
    self.player2.copy_powerups_from(self.player1)
