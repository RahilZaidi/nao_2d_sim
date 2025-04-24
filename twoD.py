import random
import pygame
import math
import time
from passing_strategy import PassingStrategy
from collision_handler import FallRecovery, CollisionHandler


f_length = 900   
f_width = 600     
g_width = 260      
g_depth = 60       
pen_area_width = 500  
pen_area_depth = 200 
circle_rad = 75  
GAME_DURATION = 120

class Player:
    def __init__(self, x, y, team, color, player_type, all_players_ref=None):
        self.x = x
        self.y = y
        self.original_x = x
        self.original_y = y
        self.team = team
        self.color = color
        self.original_color = color
        self.player_type = player_type
        self.base_player_type = player_type
        self.speed = self.set_speed()
        self.radius = 12
        self.is_active_pursuer = False
        self._all_players_ref = all_players_ref
        self.shots_attempted = 0
        
        self.target_x = x
        self.target_y = y
        self.facing_angle = 0
        self.turn_complete = True
        self.turn_start_time = 0
        self.movement_state = "idle"
        self.turn_duration = 0
        

        self.is_throwing_in = False
        self.throw_start_time = 0
        self.throw_duration = 2
        

        self.fall_recovery = FallRecovery(self)
        
        self.assigned_corner = None
        if self.team == 'red' and self.player_type == 'defender':
            if self.y < f_width / 2:
                self.assigned_corner = (0, 100)
            else:
                self.assigned_corner = (0, f_width - 100 )

    def set_speed(self):
        return {'goalkeeper': 2, 'defender': 2, 'attacker': 2}[self.player_type]

    def get_zone_limits(self):
        half_field = f_length // 2
        if self.team == 'red':
            if self.player_type == 'goalkeeper':
                return (0, pen_area_depth, (f_width-g_width)//2, (f_width+g_width)//2)
            elif self.player_type == 'defender':
                return (pen_area_depth, half_field, 0, f_width)
            else:  
                return (half_field -100, f_length, 0, f_width)
        else:  
            if self.player_type == 'goalkeeper':
                return (f_length-pen_area_depth, f_length, 
                        (f_width-g_width)//2, (f_width+g_width)//2)
            elif self.player_type == 'defender':
                return (half_field, f_length-pen_area_depth, 0, f_width)
            else:
                return (0, half_field+100, 0, f_width)
    
    def throw_in(self, ball, throw_target_x, throw_target_y):
        if time.time() - self.throw_start_time < self.throw_duration:

            return
        

        self.is_throwing_in = False
        

        angle = math.atan2(throw_target_y - ball.y, throw_target_x - ball.x)
        throw_power = 3
        

        angle += math.radians(random.uniform(-10, 10))
        
        ball.velocity_x = math.cos(angle) * throw_power
        ball.velocity_y = math.sin(angle) * throw_power
        ball.last_movement_time = time.time()
    
    def avoid_opponent_while_dribbling(self, ball, players, goal_x, goal_y):
       
        THREAT_RADIUS = 100  
        AVOIDANCE_WEIGHT = 0.7 
        
        closest_opponent = None
        min_distance = float('inf')
        
        for opponent in players:
            if opponent.team != self.team:  
                distance = math.hypot(self.x - opponent.x, self.y - opponent.y)
                if distance < min_distance and distance < THREAT_RADIUS and opponent.x > self.x:
                    min_distance = distance
                    closest_opponent = opponent
        
        if closest_opponent is None:
            return None
        

        dx = closest_opponent.x - self.x
        dy = closest_opponent.y - self.y
        angle_to_opponent = math.atan2(dy, dx)
        

        avoid_angle_left = angle_to_opponent + math.pi / 2
        avoid_angle_right = angle_to_opponent - math.pi / 2
        

        goal_angle = math.atan2(goal_y - self.y, goal_x - self.x)
        

        def normalize_angle(angle):
            return ((angle + math.pi) % (2 * math.pi)) - math.pi
        
        diff_left = abs(normalize_angle(avoid_angle_left - goal_angle))
        diff_right = abs(normalize_angle(avoid_angle_right - goal_angle))
        avoid_angle = avoid_angle_left if diff_left < diff_right else avoid_angle_right
        

        new_angle = AVOIDANCE_WEIGHT * avoid_angle + (1 - AVOIDANCE_WEIGHT) * goal_angle
        

        new_angle = normalize_angle(new_angle)
        
        return new_angle

    def move(self, ball, players):

        if self.fall_recovery.is_recovering():
            return
            
        if self.is_throwing_in:

            return
            
        x_min, x_max, y_min, y_max = self.get_zone_limits()
        
        BOUNDARY_BUFFER = 20  
        DECELERATION_DISTANCE = 50  
        

        if self.player_type == 'goalkeeper':
            if (self.team == 'red' and ball.x < pen_area_depth) or \
               (self.team == 'blue' and ball.x > f_length - pen_area_depth):
                self.target_x = ball.x
                self.target_y = ball.y
            else:
                self.target_x = (x_min + x_max) // 2
                self.target_y = ball.y
            
            self.target_x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, self.target_x))
            self.target_y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, self.target_y))
            
        elif self.is_active_pursuer:
            self.target_x = ball.x
            self.target_y = ball.y
            
            self.target_x = max(x_min + BOUNDARY_BUFFER, 
                         min(x_max - BOUNDARY_BUFFER, self.target_x))
            self.target_y = max(y_min + BOUNDARY_BUFFER,
                         min(y_max - BOUNDARY_BUFFER, self.target_y))
        elif self.team == 'red' and self.player_type == 'defender':

            attacker = next((p for p in players if p.team == 'red' and p.player_type == 'attacker'), None)
            if attacker and self.assigned_corner:
                self.target_x = self.original_x
                self.target_y = self.original_y

                corner_x, corner_y = self.assigned_corner
                self.target_x = (corner_x + attacker.x) / 2
                self.target_y = (corner_y + attacker.y) / 2


                y_offset = 100

                if corner_y == 100:
                    self.target_x += y_offset
                else:
                    self.target_x -= y_offset


                self.target_x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, self.target_x))
                self.target_y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, self.target_y))
            else:

                self.target_x = self.original_x
                self.target_y = self.original_y
        else:
            self.target_x = self.original_x
            self.target_y = self.original_y
        


        target_angle = math.atan2(self.target_y - self.y, self.target_x - self.x)
        angle_diff = self.normalize_angle(target_angle - self.facing_angle)
        

        if abs(angle_diff) > math.radians(15) and self.movement_state != "turning":
            self.movement_state = "turning"
            self.turn_start_time = time.time()
            self.turn_duration = abs(angle_diff) / math.radians(90) * 1.0
            return
            

        if self.movement_state == "turning":
            if time.time() - self.turn_start_time >= self.turn_duration:
                self.facing_angle = target_angle
                self.movement_state = "walking"
            return
        

        distance = math.hypot(self.target_x - self.x, self.target_y - self.y)
        

        speed = self.speed
        if distance < DECELERATION_DISTANCE:
            speed = self.speed * (distance/DECELERATION_DISTANCE)
        

        new_x = self.x + math.cos(self.facing_angle) * speed
        new_y = self.y + math.sin(self.facing_angle) * speed
        

        self.x = self.lerp(self.x, new_x, 0.3)
        self.y = self.lerp(self.y, new_y, 0.3)
        

        self.x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, self.x))
        self.y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, self.y))
        
        passing_strategy = PassingStrategy()
        distance_to_goal = None

        if math.hypot(self.x-ball.x, self.y-ball.y) <= self.radius + ball.radius:

            passing_strategy = PassingStrategy()


            if self.team == 'red':
                target_x = f_length
                target_y = f_width / 2
            else:
                target_x = 0
                target_y = f_width / 2


            distance_to_goal = math.hypot(self.x - target_x, self.y - target_y)


            in_opponent_half = (self.team == 'red' and self.x > f_length / 2) or \
                              (self.team == 'blue' and self.x < f_length / 2)


            if self.player_type == 'attacker' and in_opponent_half and distance_to_goal > 200 and self.team == "red":

                dribble_power = 0.5
                

                target_x, target_y = passing_strategy.find_best_pass_target(self, ball, players)
                if self.team == 'red':
                    target_x -= 50
                

                avoid_angle = self.avoid_opponent_while_dribbling(ball, players, target_x, target_y)
                
                if avoid_angle is not None:

                    angle = avoid_angle
                else:

                    angle = math.atan2(target_y - ball.y, target_x - ball.x)
                
                angle += math.radians(random.uniform(-10, 10))
                
                ball.velocity_x = math.cos(angle) * dribble_power
                ball.velocity_y = math.sin(angle) * dribble_power
                ball.last_movement_time = time.time()
            else:

                if self.team == 'red':
                    target_x, target_y = passing_strategy.find_best_pass_target(self, ball, players)
                    if self.player_type == "attacker":
                        target_x -= 50
                else:
                    target_x, target_y = passing_strategy.find_best_pass_target(self, ball, players)
                

                kick_power = 3 if self.player_type == 'attacker' and distance_to_goal <= 200 else 2
                kick_power = kick_power if self.player_type == 'attacker' else (2 if self.player_type == 'goalkeeper' else 2)
                if self.player_type == 'attacker' and self.team == 'red' and distance_to_goal <= 200:
                    self.shots_attempted += 1

                angle = math.atan2(target_y - ball.y, target_x - ball.x)
                

                angle += math.radians(random.uniform(-5, 5))
                
                ball.velocity_x = math.cos(angle) * kick_power
                ball.velocity_y = math.sin(angle) * kick_power
                ball.last_movement_time = time.time()

    def normalize_angle(self, angle):
        return ((angle + math.pi) % (2 * math.pi)) - math.pi
    
    def lerp(self, a, b, t):
        return a + (b - a) * min(max(t, 0), 1)

    def draw(self, screen):

        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        

        if not self.fall_recovery.is_recovering():
            direction_x = self.x + math.cos(self.facing_angle) * self.radius
            direction_y = self.y + math.sin(self.facing_angle) * self.radius
            pygame.draw.line(screen, (255, 255, 255), (self.x, self.y), (direction_x, direction_y), 2)
            
            if self.player_type == 'goalkeeper':
                pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius//2)
            elif self.is_active_pursuer:
                pygame.draw.line(screen, (255, 255, 255), (self.x-10, self.y), (self.x+10, self.y), 2)
        

        if self.is_throwing_in:

            arm_length = self.radius * 1.5
            pygame.draw.line(screen, (255, 255, 0), (self.x-5, self.y), (self.x-5, self.y-arm_length), 2)
            pygame.draw.line(screen, (255, 255, 0), (self.x+5, self.y), (self.x+5, self.y-arm_length), 2)
            

        self.fall_recovery.draw_recovery_animation(screen)

    def update_player_type(self, new_type):
        if new_type != self.player_type:
            self.player_type = new_type
            self.speed = self.set_speed()

            self.update_position_for_new_type()
    
    def update_position_for_new_type(self):
        x_min, x_max, y_min, y_max = self.get_zone_limits()

        if self.team == 'red':
            if self.player_type == 'defender':
                self.original_x = 200
            elif self.player_type == 'attacker':
                self.original_x = 400
                
    def get_all_players(self):
        """Get reference to all players in the simulation"""
        if self._all_players_ref is not None:
            return self._all_players_ref()
        return []
        
    def set_all_players_accessor(self, accessor_func):
        """Set a function that returns all players in the simulation"""
        self._all_players_ref = accessor_func

class Ball:
    def __init__(self, x, y):
        self.reset(x, y)
        self.last_movement_time = time.time()
        self.last_position = (x, y)
        self.stall_threshold = 6 
        self.movement_threshold = 5
        self.out_of_bounds = False
        self.last_touch_team = None
    
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_movement_time = time.time()
        self.last_position = (x, y)
        self.out_of_bounds = False
    
    def move(self):
        previous_x = self.x
        previous_y = self.y
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        current_position = (self.x, self.y)
        distance_moved = math.hypot(
            current_position[0] - self.last_position[0],
            current_position[1] - self.last_position[1]
        )
        
        if distance_moved > self.movement_threshold:
            self.last_movement_time = time.time()
            self.last_position = current_position
        

        self.velocity_x *= 0.99
        self.velocity_y *= 0.99
        
        goal_y_start = (f_width - g_width) // 2
        goal_y_end = goal_y_start + g_width
        

        if self.y - self.radius <= 0:

            self.velocity_y = 0
            self.velocity_x = 0
            self.y = self.radius
            self.out_of_bounds = True
            self.out_of_bounds_position = (self.x, self.radius)
            
        elif self.y + self.radius >= f_width:

            self.velocity_y = 0
            self.velocity_x = 0
            self.y = f_width - self.radius
            self.out_of_bounds = True
            self.out_of_bounds_position = (self.x, f_width - self.radius)
            

        if self.x - self.radius <= 0:
            if goal_y_start <= self.y <= goal_y_end:

                pass
            else:

                self.velocity_x = 0
                self.velocity_y = 0
                self.x = self.radius
                self.out_of_bounds = True
                self.out_of_bounds_position = (self.radius, self.y)
                
        elif self.x + self.radius >= f_length:
            if goal_y_start <= self.y <= goal_y_end:

                pass
            else:

                self.velocity_x = 0
                self.velocity_y = 0
                self.x = f_length - self.radius
                self.out_of_bounds = True
                self.out_of_bounds_position = (f_length - self.radius, self.y)
    
    def is_ball_stuck(self):
        return time.time() - self.last_movement_time > self.stall_threshold
        
    def register_touch(self, player):
        """Register which team last touched the ball"""
        self.last_touch_team = player.team

class FootballSimulation:
    def __init__(self, red_defenders=0, red_attackers=3, blue_defenders=2, blue_attackers=1):
        pygame.init()
        self.screen = pygame.display.set_mode((f_length, f_width))
        pygame.display.set_caption("Robot Soccer Simulation")
        
        self.red_score = 0
        self.blue_score = 0
        self.start_time = time.time()
        self.game_over = False
        self.players = []
        self.red_attacker_goals = 0  
        
        self.initialize_players(red_defenders, red_attackers, blue_defenders, blue_attackers)
        self.ball = Ball(f_length//2, f_width//2)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.game_state = "playing"
        self.throw_in_team = None
        self.throw_in_position = None
        self.throw_in_player = None
        

        self.collision_handler = CollisionHandler()
    
    def initialize_players(self, red_def, red_att, blue_def, blue_att):
        if red_def + red_att != 3 or blue_def + blue_att != 3:
            raise ValueError("Each team must have 3 outfield players (defenders + attackers)")
        
        self.players.append(Player(50, f_width//2, 'red', (255,0,0), 'goalkeeper'))
        for i in range(red_def):
            self.players.append(Player(200+((i+1)*50), (i+1)*(f_width//(red_def+1)), 'red', (255,100,0), 'defender'))
    

        for i in range(red_att):
            self.players.append(Player(400, (i+1)*(f_width//(red_att+1)), 'red', (255,50,0), 'attacker'))
    

        self.players.append(Player(850, f_width//2, 'blue', (0,0,255), 'goalkeeper'))
        for i in range(blue_def):
            self.players.append(Player(700, (i+1)*(f_width//(blue_def+1)), 'blue', (0,100,255), 'defender'))
        for i in range(blue_att):
            self.players.append(Player(600, (i+1)*(f_width//(blue_att+1)), 'blue', (0,150,255), 'attacker'))
            

        for player in self.players:
            player.set_all_players_accessor(lambda: self.players)

    def update_pursuers(self):
        red_players = [p for p in self.players if p.team == 'red' and p.player_type != 'goalkeeper']
        blue_players = [p for p in self.players if p.team == 'blue' and p.player_type != 'goalkeeper']
        

        def is_ball_in_player_zone(player):
            x_min, x_max, y_min, y_max = player.get_zone_limits()
            zone_buffer = 50
            return (x_min - zone_buffer <= self.ball.x <= x_max + zone_buffer and 
                    y_min - zone_buffer <= self.ball.y <= y_max + zone_buffer)
        

        accessible_red_players = [p for p in red_players if is_ball_in_player_zone(p)]
        accessible_blue_players = [p for p in blue_players if is_ball_in_player_zone(p)]
        

        for p in red_players + blue_players:
            p.is_active_pursuer = False
        

        if accessible_red_players:
            red_closest = min(accessible_red_players, key=lambda p: math.hypot(p.x-self.ball.x, p.y-self.ball.y))
            red_closest.is_active_pursuer = True
        elif red_players:
            red_closest = min(red_players, key=lambda p: math.hypot(p.x-self.ball.x, p.y-self.ball.y))
            red_closest.is_active_pursuer = True
            

        if accessible_blue_players:
            blue_closest = min(accessible_blue_players, key=lambda p: math.hypot(p.x-self.ball.x, p.y-self.ball.y))
            blue_closest.is_active_pursuer = True
        elif blue_players:
            blue_closest = min(blue_players, key=lambda p: math.hypot(p.x-self.ball.x, p.y-self.ball.y))
            blue_closest.is_active_pursuer = True

    def check_goal(self):
        goal_y_start = (f_width - g_width) // 2
        

        if 0 <= self.ball.x <= g_depth and goal_y_start <= self.ball.y <= goal_y_start + g_width:
            self.blue_score += 1
            self.reset_after_goal()
            return True
        

        if f_length-g_depth <= self.ball.x <= f_length and goal_y_start <= self.ball.y <= goal_y_start + g_width:
            self.red_score += 1
            last_touch_player = next((p for p in self.players if p.team == self.ball.last_touch_team), None)
            if last_touch_player and last_touch_player.team == 'red' and last_touch_player.player_type == 'attacker':
                self.red_attacker_goals += 1
            self.reset_after_goal()
            return True
        
        return False
    
    def get_attacker_stats(self):
        red_attacker_shots = sum(p.shots_attempted for p in self.players 
                                if p.team == 'red' and p.player_type == 'attacker')
        return {
            'red_attacker_goals': self.red_attacker_goals,
            'red_attacker_shots': red_attacker_shots
        }
        
    def reset_after_goal(self):
        self.ball.reset(f_length//2, f_width//2)
        for player in self.players:
            player.x = player.original_x
            player.y = player.original_y
            player.is_active_pursuer = False
        self.game_state = "playing"

    def draw_field(self):
        self.screen.fill((0, 200, 0))
        

        pygame.draw.rect(self.screen, (255,255,255), (0, 0, f_length, f_width), 2)
        pygame.draw.line(self.screen, (255,255,255), (f_length//2, 0), (f_length//2, f_width), 2)
        pygame.draw.circle(self.screen, (255,255,255), (f_length//2, f_width//2), circle_rad, 2)
        

        pygame.draw.rect(self.screen, (255,255,255), 
                         (0, (f_width-pen_area_width)//2, pen_area_depth, pen_area_width), 2)
        pygame.draw.rect(self.screen, (255,255,255), 
                         (f_length-pen_area_depth, (f_width-pen_area_width)//2, 
                          pen_area_depth, pen_area_width), 2)
        

        pygame.draw.rect(self.screen, (255,255,255), 
                         (0, (f_width-g_width)//2, g_depth, g_width), 2)
        pygame.draw.rect(self.screen, (255,255,255), 
                         (f_length-g_depth, (f_width-g_width)//2, g_depth, g_width), 2)
        

        elapsed = max(0, GAME_DURATION - (time.time() - self.start_time))
        score_text = f"Red {self.red_score} - {self.blue_score} Blue    Time: {elapsed//60:.0f}:{elapsed%60:02.0f}"
        text = self.font.render(score_text, True, (255,255,255))
        self.screen.blit(text, (f_length//2 - text.get_width()//2, 10))
        

        collision_text = f"Collisions: {self.collision_handler.get_collision_count()}"
        c_text = self.font.render(collision_text, True, (255, 255, 0))
        self.screen.blit(c_text, (f_length - c_text.get_width() - 10, 10))
        

        if self.game_state == "throw_in":
            state_text = f"Throw-in: {self.throw_in_team.upper()} team"
            text = self.font.render(state_text, True, (255, 255, 0))
            self.screen.blit(text, (f_length//2 - text.get_width()//2, 40))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            if not self.game_over:
                if time.time() - self.start_time >= GAME_DURATION:
                    self.game_over = True
                    print(f"Final Score: Red {self.red_score} - {self.blue_score} Blue")
                    print(f"Total Collisions: {self.collision_handler.get_collision_count()}")
                

                if self.game_state == "playing":
                    self.update_pursuers()
                    

                    self.collision_handler.check_and_handle_player_collisions(self.players)
                    

                    for player in self.players:
                        if math.hypot(player.x-self.ball.x, player.y-self.ball.y) <= player.radius + self.ball.radius:
                            self.ball.register_touch(player)
                        

                        player.move(self.ball, self.players)
                    
                    self.ball.move()
                    

                    if self.ball.out_of_bounds:
                        self.reset_after_goal()
                    
                    if self.ball.is_ball_stuck():
                        print("Ball reset due to stalling")
                        self.reset_after_goal()
                        
                    if self.check_goal():
                        self.update_pursuers()
            
            self.draw_field()
            

            self.collision_handler.draw_collision_indicators(self.screen)
            

            for player in self.players:
                player.draw(self.screen)
                

            pygame.draw.circle(self.screen, (255,255,255), (int(self.ball.x), int(self.ball.y)), self.ball.radius)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    simulation = FootballSimulation(red_defenders=2, red_attackers=1, 
                                  blue_defenders=2, blue_attackers=1)
    simulation.run()
