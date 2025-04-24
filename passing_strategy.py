import math

class PassingStrategy:
    def __init__(self):
        self.field_length = 900
        self.field_width = 600
    
    def find_best_pass_target(self, player, ball, all_players):
        
        if player.team == 'red':
            target_x = self.field_length  # Right goal
            target_y = self.field_width / 2
        else:
            target_x = 0  # Left goal
            target_y = self.field_width / 2
            
        if player.player_type == 'attacker':
            if player.team == 'red':
                goal_x = self.field_length
            else:
                goal_x = 0
            goal_y = self.field_width / 2
                
            dist_to_goal = math.hypot(goal_x - player.x, goal_y - player.y)
            
            # If close to goal shoot
            if dist_to_goal < 150:
                return target_x, target_y
        
        # Get teammates
        teammates = [p for p in all_players if p.team == player.team and p != player]
        opponents = [p for p in all_players if p.team != player.team]
        
        # For attackers,  forward passes
        if player.player_type == 'attacker':
            if player.team == 'red':
                potential_receivers = [t for t in teammates if t.x > player.x + 20]
            else:
                potential_receivers = [t for t in teammates if t.x < player.x - 20]
                
            # If no forward options, pass to all teammates
            if not potential_receivers:
                if player.player_type == 'attacker':
                    return target_x,target_y
                potential_receivers = teammates
        else:
            potential_receivers = teammates
        
        best_receiver = None
        best_score = float('-inf')
        
        for receiver in potential_receivers:
            if abs(receiver.y - player.y) < 50:
                continue
                
            distance = math.hypot(receiver.x - player.x, receiver.y - player.y)
            
            pass_blocked = False
            for opponent in opponents:
               
                min_x = min(player.x, receiver.x) - 30
                max_x = max(player.x, receiver.x) + 30
                min_y = min(player.y, receiver.y) - 30
                max_y = max(player.y, receiver.y) + 30
                
                if (min_x <= opponent.x <= max_x and min_y <= opponent.y <= max_y):
                    if self.is_point_near_line(player.x, player.y, receiver.x, receiver.y, 
                                               opponent.x, opponent.y, 40):
                        pass_blocked = True
                        break
            
            if pass_blocked:
                continue
                
            score = 1000 - distance
            
            if player.player_type == 'attacker':
                if (player.team == 'red' and receiver.x > player.x) or (player.team == 'blue' and receiver.x < player.x):
                    score += 500
            
            if score > best_score:
                best_score = score
                best_receiver = receiver
        
        if best_receiver:
            return best_receiver.x, best_receiver.y
        
        return target_x, target_y
    
    def is_point_near_line(self, x1, y1, x2, y2, px, py, threshold):
        line_length = math.hypot(x2 - x1, y2 - y1)
        
        if line_length == 0:
            return math.hypot(px - x1, py - y1) <= threshold
            
        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_length * line_length)
        t = max(0, min(1, t)) 
        
        nearest_x = x1 + t * (x2 - x1)
        nearest_y = y1 + t * (y2 - y1)
        
        distance = math.hypot(px - nearest_x, py - nearest_y)
        
        return distance <= threshold