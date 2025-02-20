import random
import pygame
import math
import time

f_length = 900   
f_width = 600     
g_width = 260      
g_depth = 60       
pen_area_width = 500  
pen_area_depth = 200 
circle_rad = 75  
GAME_DURATION = 60  

class Player:
    def __init__(self, x, y, team, color, player_type):
        self.x = x
        self.y = y
        self.original_x = x
        self.original_y = y
        self.team = team
        self.color = color
        self.player_type = player_type
        self.speed = self.set_speed()
        self.radius = 12
        self.is_active_pursuer = False

    def set_speed(self):
        return {'goalkeeper': 4, 'defender': 4, 'attacker': 4}[self.player_type]

    def get_zone_limits(self):
        half_field = f_length // 2
        if self.team == 'red':
            if self.player_type == 'goalkeeper':
                return (0, pen_area_depth, (f_width-g_width)//2, (f_width+g_width)//2)
            elif self.player_type == 'defender':
                return (pen_area_depth, half_field, 0, f_width)
            else:  
                return (half_field, f_length, 0, f_width)
        else:  
            if self.player_type == 'goalkeeper':
                return (f_length-pen_area_depth, f_length, 
                        (f_width-g_width)//2, (f_width+g_width)//2)
            elif self.player_type == 'defender':
                return (half_field, f_length-pen_area_depth, 0, f_width)
            else:  # attacker
                return (0, half_field+20, 0, f_width)
    
    def calculate_defensive_position(self, players):
        opposite_team = 'blue' if self.team == 'red' else 'red'
        attackers = [p for p in players if p.team == opposite_team and p.player_type == 'attacker']
        
        if not attackers:
            return self.original_x, self.original_y

        avg_attacker_x = sum(a.x for a in attackers) / len(attackers)
        avg_attacker_y = sum(a.y for a in attackers) / len(attackers)

        if self.team == 'red':
            corner_x = pen_area_depth
            corner_y = self.y  
        else:
            corner_x = f_length - pen_area_depth
            corner_y = self.y  

        target_x = (avg_attacker_x + corner_x) / 2
        target_y = (avg_attacker_y + corner_y) / 2

        x_min, x_max, y_min, y_max = self.get_zone_limits()
        target_x = max(x_min, min(x_max, target_x))
        target_y = max(y_min, min(y_max, target_y))

        return target_x, target_y

    def move(self, ball, players):
        x_min, x_max, y_min, y_max = self.get_zone_limits()
        
        BOUNDARY_BUFFER = 20  
        DECELERATION_DISTANCE = 50  
        
        x_min, x_max, y_min, y_max = self.get_zone_limits()
        
        if self.player_type == 'goalkeeper':
            if (self.team == 'red' and ball.x < pen_area_depth) or \
               (self.team == 'blue' and ball.x > f_length - pen_area_depth):
                target_x = ball.x
                target_y = ball.y
            else:
                target_x = (x_min + x_max) // 2
                target_y = (y_min + y_max) // 2
            
            target_x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, target_x))
            target_y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, target_y))
            
            angle = math.atan2(target_y - self.y, target_x - self.x)
            distance = math.hypot(target_x - self.x, target_y - self.y)
            speed = self.speed * 1.5 * min(1, distance/DECELERATION_DISTANCE)
            
            new_x = self.x + math.cos(angle) * speed
            new_y = self.y + math.sin(angle) * speed

        elif self.is_active_pursuer:
            target_x = ball.x
            target_y = ball.y
            
            target_x = max(x_min + BOUNDARY_BUFFER, 
                         min(x_max - BOUNDARY_BUFFER, target_x))
            target_y = max(y_min + BOUNDARY_BUFFER,
                         min(y_max - BOUNDARY_BUFFER, target_y))

            angle = math.atan2(target_y - self.y, target_x - self.x)
            distance = math.hypot(target_x - self.x, target_y - self.y)
            
            speed = self.speed * min(1, distance/DECELERATION_DISTANCE)
            
            new_x = self.x + math.cos(angle) * speed
            new_y = self.y + math.sin(angle) * speed
            

        else:
            angle = math.atan2(self.original_y - self.y, self.original_x - self.x)
            distance = math.hypot(self.original_x - self.x, self.original_y - self.y)
            speed = self.speed * min(1, distance/DECELERATION_DISTANCE)
            
            new_x = self.x + math.cos(angle) * speed
            new_y = self.y + math.sin(angle) * speed

        # smoother pos updates 
        self.x = self.lerp(self.x, new_x, 0.3)
        self.y = self.lerp(self.y, new_y, 0.3)
        self.x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, self.x))
        self.y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, self.y))

        self.x = max(x_min, min(x_max, new_x))
        self.y = max(y_min, min(y_max, new_y))

        # kick ball 
        if math.hypot(self.x-ball.x, self.y-ball.y) <= self.radius + ball.radius:
            if self.team == 'red':
                target_x = f_length  
                target_y = f_width / 2
            else:
                target_x = 0  
                target_y = f_width / 2

            angle = math.atan2(target_y - ball.y, target_x - ball.x)
            kick_power = 6 if self.player_type == 'attacker' else (15 if self.player_type == 'goalkeeper' else 10)            
            # Adding some random to shots
            angle += math.radians(random.uniform(-15, 15))
            #Making GK Kick to the Ends
            if self.player_type == "goalkeeper":
                angle += math.radians(random.choice([30, -30]))
            
            ball.velocity_x = math.cos(angle) * kick_power
            ball.velocity_y = math.sin(angle) * kick_power

    
    
    def lerp(self, a, b, t):
        return a + (b - a) * min(max(t, 0), 1)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        if self.player_type == 'goalkeeper':
            pygame.draw.circle(screen, (255,255,255), (int(self.x), int(self.y)), self.radius//2)
        elif self.is_active_pursuer:
            pygame.draw.line(screen, (255,255,255), (self.x-10, self.y), (self.x+10, self.y), 2)

class Ball:
    def __init__(self, x, y):
        self.reset(x, y)
        self.last_movement_time = time.time()
        self.last_position = (x, y)
        self.stall_threshold = 3 
        self.movement_threshold = 5  
    
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_movement_time = time.time()
        self.last_position = (x, y)
    
    def move(self):
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
        
        # Add friction like real life
        self.velocity_x *= 0.99
        self.velocity_y *= 0.99
        
        goal_y_start = (f_width - g_width) // 2
        goal_y_end = goal_y_start + g_width
        
        # Check for goals and  boundaries
        if self.x - self.radius <= 0:
            if goal_y_start <= self.y <= goal_y_end:
                pass
            else:
                self.velocity_x *= -0.8
                self.x = self.radius
        elif self.x + self.radius >= f_length:
            if goal_y_start <= self.y <= goal_y_end:
                pass
            else:
                self.velocity_x *= -0.8
                self.x = f_length - self.radius
        
        if self.y - self.radius <= 0:
            self.velocity_y *= -0.8
            self.y = self.radius
        elif self.y + self.radius >= f_width:
            self.velocity_y *= -0.8
            self.y = f_width - self.radius
    
    def is_ball_stuck(self):
        return time.time() - self.last_movement_time > self.stall_threshold

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
        
        self.initialize_players(red_defenders, red_attackers, blue_defenders, blue_attackers)
        self.ball = Ball(f_length//2, f_width//2)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)

    def initialize_players(self, red_def, red_att, blue_def, blue_att):
        if red_def + red_att != 3 or blue_def + blue_att != 3:
            raise ValueError("Each team must have 3 outfield players (defenders + attackers)")
        
        # Red team
        self.players.append(Player(50, f_width//2, 'red', (255,0,0), 'goalkeeper'))
        for i in range(red_def):
            self.players.append(Player(200, (i+1)*(f_width//(red_def+1)), 'red', (255,100,0), 'defender'))
        for i in range(red_att):
            self.players.append(Player(400, (i+1)*(f_width//(red_att+1)), 'red', (255,150,0), 'attacker'))
        
        # Blue team
        self.players.append(Player(850, f_width//2, 'blue', (0,0,255), 'goalkeeper'))
        for i in range(blue_def):
            self.players.append(Player(700, (i+1)*(f_width//(blue_def+1)), 'blue', (0,100,255), 'defender'))
        for i in range(blue_att):
            self.players.append(Player(600, (i+1)*(f_width//(blue_att+1)), 'blue', (0,150,255), 'attacker'))

    def update_pursuers(self):
        red_players = [p for p in self.players if p.team == 'red' and p.player_type != 'goalkeeper']
        blue_players = [p for p in self.players if p.team == 'blue' and p.player_type != 'goalkeeper']
        
        if red_players:
            red_closest = min(red_players, key=lambda p: math.hypot(p.x-self.ball.x, p.y-self.ball.y))
            for p in red_players:
                p.is_active_pursuer = (p == red_closest)
        
        if blue_players:
            blue_closest = min(blue_players, key=lambda p: math.hypot(p.x-self.ball.x, p.y-self.ball.y))
            for p in blue_players:
                p.is_active_pursuer = (p == blue_closest)

    def check_goal(self):
        goal_y_start = (f_width - g_width) // 2
        
        # Blue scores in red goal
        if 0 <= self.ball.x <= g_depth and goal_y_start <= self.ball.y <= goal_y_start + g_width:
            self.blue_score += 1
            self.reset_after_goal()
            return True
        
        # Red scores in blue goal
        if f_length-g_depth <= self.ball.x <= f_length and goal_y_start <= self.ball.y <= goal_y_start + g_width:
            self.red_score += 1
            self.reset_after_goal()
            return True
        
        return False

    def reset_after_goal(self):
        self.ball.reset(f_length//2, f_width//2)
        for player in self.players:
            player.x = player.original_x
            player.y = player.original_y
            player.is_active_pursuer = False

    def draw_field(self):
        self.screen.fill((0, 200, 0))  # Field color
        
        # Field markings
        pygame.draw.rect(self.screen, (255,255,255), (0, 0, f_length, f_width), 2)
        pygame.draw.line(self.screen, (255,255,255), (f_length//2, 0), (f_length//2, f_width), 2)
        pygame.draw.circle(self.screen, (255,255,255), (f_length//2, f_width//2), circle_rad, 2)
        
        # Penalty areas
        pygame.draw.rect(self.screen, (255,255,255), 
                         (0, (f_width-pen_area_width)//2, pen_area_depth, pen_area_width), 2)
        pygame.draw.rect(self.screen, (255,255,255), 
                         (f_length-pen_area_depth, (f_width-pen_area_width)//2, 
                          pen_area_depth, pen_area_width), 2)
        
        # Goals
        pygame.draw.rect(self.screen, (255,255,255), 
                         (0, (f_width-g_width)//2, g_depth, g_width), 2)
        pygame.draw.rect(self.screen, (255,255,255), 
                         (f_length-g_depth, (f_width-g_width)//2, g_depth, g_width), 2)
        
        # Score and time
        elapsed = max(0, GAME_DURATION - (time.time() - self.start_time))
        score_text = f"Red {self.red_score} - {self.blue_score} Blue    Time: {elapsed//60:.0f}:{elapsed%60:02.0f}"
        text = self.font.render(score_text, True, (255,255,255))
        self.screen.blit(text, (f_length//2 - text.get_width()//2, 10))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            if not self.game_over:
                if time.time() - self.start_time >= GAME_DURATION:
                    self.game_over = True
                    print(f"Final Score: Red {self.red_score} - {self.blue_score} Blue")
                
                self.update_pursuers()
                for player in self.players:
                        player.move(self.ball, self.players)
                    


                self.ball.move()
                if self.ball.is_ball_stuck():
                    print("Ball reset due to stalling")
                    self.reset_after_goal()  # Reuse existing reset function
                if self.check_goal():
                    self.update_pursuers()
            
            self.draw_field()
            for player in self.players:
                player.draw(self.screen)
            pygame.draw.circle(self.screen, (255,255,255), (int(self.ball.x), int(self.ball.y)), self.ball.radius)
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    simulation = FootballSimulation(red_defenders=1, red_attackers=2, 
                                  blue_defenders=2, blue_attackers=1)
    simulation.run()