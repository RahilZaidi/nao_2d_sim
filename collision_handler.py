import time
import pygame

class FallRecovery:
    """
    Handles the collision detection and fall recovery animation for Nao robots.
    When robots collide, they turn yellow and take 2 seconds to recover.
    """
    def __init__(self, player):
        self.player = player
        self.is_fallen = False
        self.fall_start_time = 0
        self.recovery_duration = 2.0  # 2 seconds to get up
        
        # IMPORTANT: Capture original color on initialization
        # Store as a tuple to prevent reference issues
        if hasattr(player, 'color'):
            r, g, b = player.color
            self.original_color = (r, g, b)
        else:
            # Default color in case player doesn't have a color attribute
            self.original_color = (255, 0, 0) if player.team == 'red' else (0, 0, 255)
            
        # Set fallen color - same for both teams
        self.fallen_color = (255, 255, 0)  # Yellow color for fallen state
        self.fall_position = None  # Store position where robot fell
        
        # Debug info
        self.debug_last_update_time = time.time()
        self.debug_recovery_progress = 0.0
        
        print(f"Initialized FallRecovery for {player.team} player with original color {self.original_color}")

    def check_collision(self, other_players):
        """Check for collisions with other players"""
        # Skip if already fallen
        if self.is_fallen:
            return
            
        # Check collision with other players
        for other in other_players:
            if other is self.player:
                continue
                
            # Ignore if other player is already fallen
            if hasattr(other, 'fall_recovery') and other.fall_recovery.is_recovering():
                continue
                
            # Calculate distance between players
            distance = ((self.player.x - other.x) ** 2 + (self.player.y - other.y) ** 2) ** 0.5
            
            # If collision detected
            if distance < (1.5):
                self.fall_down()
                
                # Make collision mutual - both players fall down
                if hasattr(other, 'fall_recovery') and not other.fall_recovery.is_recovering():
                    other.fall_recovery.fall_down()
                    print(f"Both players fell down: {self.player.team} and {other.team}")
                
                return

    def fall_down(self):
        """Trigger the fall animation"""
        # Prevent duplicate fall
        if self.is_fallen:
            return
            
        # Save current color if not already saved
        if not hasattr(self, 'original_color') or self.original_color is None:
            r, g, b = self.player.color
            self.original_color = (r, g, b)
            
        # Set fallen state
        self.is_fallen = True
        self.fall_start_time = time.time()
        self.player.color = self.fallen_color
        
        # Store the position where the robot fell
        self.fall_position = (self.player.x, self.player.y)
        
        print(f"{self.player.team} player fell down, original color: {self.original_color}")
        
    def update(self):
        """Update recovery state"""
        if not self.is_fallen:
            return
            
        # Check if recovery time has passed
        current_time = time.time()
        time_fallen = current_time - self.fall_start_time
        
        if time_fallen >= self.recovery_duration:
            print(f"Player recovered after {time_fallen:.2f} seconds")
            self.recover()
            
    def recover(self):
        """Reset the player to normal state after recovery and move players apart"""
        if self.is_fallen:
            # Log recovery
            print(f"Player {id(self.player)} of team {self.player.team} recovered from fall")
            print(f"  Restoring color from {self.player.color} to {self.original_color}")
            
            # Reset state
            self.is_fallen = False
            
            # Make sure we have an original color to restore
            if hasattr(self, 'original_color') and self.original_color is not None:
                self.player.color = self.original_color
            else:
                # Use team default if original color not found
                default_color = (255, 0, 0) if self.player.team == 'red' else (0, 0, 255)
                print(f"  WARNING: No original color found, using default: {default_color}")
                self.player.color = default_color
            
            # Move player away from other players to prevent immediate re-collision
            self.separate_from_nearby_players()
                
            self.fall_position = None
        else:
            print(f"Warning: recover() called but player was not fallen")
            
    def separate_from_nearby_players(self):
        """Move player away from nearby players to prevent immediate re-collision"""
        import math
        
        # Find all nearby players
        nearby_players = []
        separation_distance = 30  # Desired distance between players
        
        # Look for players that would be too close after recovery
        for other in self.player.get_all_players():
            if other is self.player:
                continue
                
            # Calculate distance between players
            distance = math.hypot(self.player.x - other.x, self.player.y - other.y)
            
            # If too close, track this player
            if distance < separation_distance:
                nearby_players.append(other)
                
        if not nearby_players:
            return  # No nearby players to separate from
            
        # If we found nearby players, move away from their average position
        if nearby_players:
            # Calculate average position of nearby players
            avg_x = sum(p.x for p in nearby_players) / len(nearby_players)
            avg_y = sum(p.y for p in nearby_players) / len(nearby_players)
            
            # Calculate direction away from average position
            dx = self.player.x - avg_x
            dy = self.player.y - avg_y
            
            # Normalize direction vector
            distance = math.hypot(dx, dy)
            if distance > 0:
                dx /= distance
                dy /= distance
            else:
                # If exactly at same position, move in random direction
                import random
                angle = random.uniform(0, 2 * math.pi)
                dx = math.cos(angle)
                dy = math.sin(angle)
            
            # Move player away (considering zone limits)
            push_distance = 35  # How far to push player away
            new_x = self.player.x + dx * push_distance
            new_y = self.player.y + dy * push_distance
            
            # Get player zone limits
            x_min, x_max, y_min, y_max = self.player.get_zone_limits()
            buffer = 20
            
            # Ensure player stays within zone limits
            new_x = max(x_min + buffer, min(x_max - buffer, new_x))
            new_y = max(y_min + buffer, min(y_max - buffer, new_y))
            
            # Apply new position
            self.player.x = new_x
            self.player.y = new_y
            
            print(f"{self.player.team} player moved to prevent re-collision: ({new_x:.1f}, {new_y:.1f})")

    def is_recovering(self):
        """Check if player is currently in recovery state"""
        return self.is_fallen
        
    def draw_recovery_animation(self, screen):
        """Draw recovery animation if player is fallen"""
        if not self.is_fallen:
            return
            
        # Calculate recovery progress (0.0 to 1.0)
        current_time = time.time()
        progress = min(1.0, (current_time - self.fall_start_time) / self.recovery_duration)
        self.debug_recovery_progress = progress
        
        # Draw recovery indicator (circular progress)
        radius = self.player.radius + 5
        rect = (int(self.player.x - radius), int(self.player.y - radius), 
                int(radius * 2), int(radius * 2))
        
        # Draw progress circle
        pygame.draw.arc(screen, (255, 255, 255), rect, 0, progress * 6.28, 2)
        
        # Draw remaining time text
        time_left = max(0, self.recovery_duration - (current_time - self.fall_start_time))
        if pygame.font:
            font = pygame.font.Font(None, 20)
            text = font.render(f"{time_left:.1f}s", True, (255, 255, 255))
            screen.blit(text, (self.player.x - 10, self.player.y - 20))
                         
        # Draw X mark if just fallen (first half of recovery)
        if progress < 0.5:
            # Draw X mark to indicate fallen state
            size = self.player.radius * 0.7
            pygame.draw.line(screen, (255, 0, 0), 
                             (self.player.x - size, self.player.y - size),
                             (self.player.x + size, self.player.y + size), 2)
            pygame.draw.line(screen, (255, 0, 0), 
                             (self.player.x + size, self.player.y - size),
                             (self.player.x - size, self.player.y + size), 2)
                             
        # Draw getting up animation (second half of recovery)
        else:
            # Draw check mark to indicate recovery
            size = self.player.radius * 0.7
            pygame.draw.line(screen, (0, 255, 0), 
                             (self.player.x - size, self.player.y),
                             (self.player.x - size/2, self.player.y + size/2), 2)
            pygame.draw.line(screen, (0, 255, 0), 
                             (self.player.x - size/2, self.player.y + size/2),
                             (self.player.x + size, self.player.y - size), 2)

class CollisionHandler:

    def __init__(self):
        self.collision_count = 0
        self.collision_positions = []  
        self.max_position_history = 5 
        
    def check_and_handle_player_collisions(self, players):
        """Check all players for collisions and handle the falling animations"""
        # First update recovery state for all players
        for player in players:
            player.fall_recovery.update()
            
        # Shuffle the order of players to avoid bias
        import random
        players_copy = players.copy()
        random.shuffle(players_copy)
        
        new_collision_positions = []
        
        # Then check for new collisions in random order
        for player in players_copy:
            previous_state = player.fall_recovery.is_recovering()
            # Only check for new collisions if not already fallen
            if not previous_state:
                player.fall_recovery.check_collision(players)
                
                # If player just fell down, track collision
                if not previous_state and player.fall_recovery.is_recovering():
                    collision_pos = (player.x, player.y)
                    
                    # Only count each collision once (at unique positions)
                    unique_collision = True
                    for pos in new_collision_positions:
                        dist = ((pos[0] - collision_pos[0])**2 + (pos[1] - collision_pos[1])**2)**0.5
                        if dist < 30:  # If positions are close, consider it the same collision
                            unique_collision = False
                            break
                    
                    if unique_collision:
                        self.collision_count += 1
                        self.collision_positions.append(collision_pos)
                        new_collision_positions.append(collision_pos)
                        # Keep only the most recent collision positions
                        if len(self.collision_positions) > self.max_position_history:
                            self.collision_positions.pop(0)
                            
        # Print team-specific collision stats (for debugging)
        fallen_red = sum(1 for p in players if p.team == 'red' and p.fall_recovery.is_recovering())
        fallen_blue = sum(1 for p in players if p.team == 'blue' and p.fall_recovery.is_recovering()) 
        if fallen_red > 0 or fallen_blue > 0:
            print(f"Currently fallen players: Red={fallen_red}, Blue={fallen_blue}")
                    
    def draw_collision_indicators(self, screen):
        """Draw collision indicators at recent collision positions"""
        for pos in self.collision_positions:
            # Draw a fading X at collision positions
            index = self.collision_positions.index(pos)
            opacity = 255 - (index * 40)  # Fade out older collisions
            if opacity > 0:
                # Draw an X mark
                pygame.draw.line(screen, (255, 0, 0, opacity), 
                                (pos[0] - 15, pos[1] - 15),
                                (pos[0] + 15, pos[1] + 15), 2)
                pygame.draw.line(screen, (255, 0, 0, opacity), 
                                (pos[0] + 15, pos[1] - 15),
                                (pos[0] - 15, pos[1] + 15), 2)
    
    def get_collision_count(self):
        return self.collision_count