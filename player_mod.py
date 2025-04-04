"""
Modified Player class with powerup sharing functionality
"""

import pygame as pg
from pygame.math import Vector2 as vec
import random
import math
from settings import *

# This file contains only the modified Player class methods
# The rest of the implementation remains in sprites.py

def share_powerup_with_other_player(self, powerup_type):
    """Share a powerup with the other player"""
    other_player = None
    if self.player_num == 1 and self.game.player2.alive():
        other_player = self.game.player2
    elif self.player_num == 2 and self.game.player1.alive():
        other_player = self.game.player1
        
    if other_player:
        other_player.apply_powerup(powerup_type)
        print(f"Powerup {powerup_type} shared with Player {other_player.player_num}")

def check_powerup_collisions_mod(self):
    """Check if player has collected any powerups and share them with the other player"""
    hits = pg.sprite.spritecollide(self, self.game.powerups, True)
    for powerup in hits:
        # Apply to self
        self.apply_powerup(powerup.type)
        
        # Share with other player
        share_powerup_with_other_player(self, powerup.type)

def copy_powerups_from_other_player(self):
    """Copy all active powerups from the other player"""
    other_player = None
    if self.player_num == 1 and self.game.player2.alive():
        other_player = self.game.player2
    elif self.player_num == 2 and self.game.player1.alive():
        other_player = self.game.player1
        
    if other_player:
        # Copy all active powerups
        for powerup_type, active in other_player.active_powerups.items():
            if active:
                self.active_powerups[powerup_type] = True
                print(f"Player {self.player_num} received {powerup_type} powerup from Player {other_player.player_num}")
        
        # Copy shield health if shield is active
        if other_player.active_powerups["shield"]:
            self.shield_health = other_player.shield_health
