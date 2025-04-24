import pygame
import math
import random
import time

# Field dimensions
f_length = 900
f_width = 600
GAME_DURATION = 120  # Not strictly enforced, just for reference

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_movement_time = time.time()

    def move(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_x *= 0.99  # Friction
        self.velocity_y *= 0.99

        # Boundary checks
        if self.x - self.radius < 0:
            self.x = self.radius
            self.velocity_x = 0
        elif self.x + self.radius > f_length:
            self.x = f_length - self.radius
            self.velocity_x = 0
        if self.y - self.radius < 0:
            self.y = self.radius
            self.velocity_y = 0
        elif self.y + self.radius > f_width:
            self.y = f_width - self.radius
            self.velocity_y = 0

        self.last_movement_time = time.time()

class Player:
    def __init__(self, x, y, team, color, player_type):
        self.x = x
        self.y = y
        self.original_x = x
        self.original_y = y
        self.team = team
        self.color = color
        self.player_type = player_type
        self.speed = 2 if player_type == 'attacker' else 2
        self.radius = 12
        self.facing_angle = 0
        self.movement_state = "idle"
        self.target_x = x
        self.target_y = y
        self.players = []
        self.position_history = [] if player_type == 'attacker' else None  # Track attacker movement

    def set_all_players(self, players):
        self.players = players

    def get_zone_limits(self):
        if self.team == 'red' and self.player_type == 'attacker':
            return (f_length // 2, f_length, 0, f_width)
        return (0, f_length, 0, f_width)  # Defender can be anywhere for simplicity

    def avoid_opponent_while_dribbling(self, ball, goal_x, goal_y):
        THREAT_RADIUS = 50
        AVOIDANCE_WEIGHT = 0.7

        closest_opponent = None
        min_distance = float('inf')

        for opponent in self.players:
            if opponent.team != self.team:
                distance = math.hypot(self.x - opponent.x, self.y - opponent.y)
                if distance < min_distance and distance < THREAT_RADIUS:
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
        return normalize_angle(new_angle)

    def move(self, ball):
        if self.player_type == 'defender':
            return  # Keep defender static

        x_min, x_max, y_min, y_max = self.get_zone_limits()
        BOUNDARY_BUFFER = 20
        DECELERATION_DISTANCE = 50

        if self.player_type == 'attacker':
            if self.x > f_length / 2:  # Opponent's half
                self.target_x = ball.x
                self.target_y = ball.y
            else:
                self.target_x = self.original_x
                self.target_y = self.original_y

        self.target_x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, self.target_x))
        self.target_y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, self.target_y))

        target_angle = math.atan2(self.target_y - self.y, self.target_x - self.x)
        angle_diff = ((target_angle - self.facing_angle + math.pi) % (2 * math.pi)) - math.pi

        if abs(angle_diff) > math.radians(15) and self.movement_state != "turning":
            self.movement_state = "turning"
            return

        if self.movement_state == "turning":
            self.facing_angle += math.copysign(math.radians(90) * 0.016, angle_diff)
            if abs(((target_angle - self.facing_angle + math.pi) % (2 * math.pi)) - math.pi) < math.radians(15):
                self.movement_state = "walking"
            return

        distance = math.hypot(self.target_x - self.x, self.target_y - self.y)
        speed = self.speed * (distance / DECELERATION_DISTANCE) if distance < DECELERATION_DISTANCE else self.speed

        new_x = self.x + math.cos(self.facing_angle) * speed
        new_y = self.y + math.sin(self.facing_angle) * speed

        self.x = self.x + 0.3 * (new_x - self.x)
        self.y = self.y + 0.3 * (new_y - self.y)

        self.x = max(x_min + BOUNDARY_BUFFER, min(x_max - BOUNDARY_BUFFER, self.x))
        self.y = max(y_min + BOUNDARY_BUFFER, min(y_max - BOUNDARY_BUFFER, self.y))

        # Store position for attacker
        if self.player_type == 'attacker':
            self.position_history.append((int(self.x), int(self.y)))

        if self.player_type == 'attacker' and math.hypot(self.x - ball.x, self.y - ball.y) <= self.radius + ball.radius:
            target_x = f_length  # Blue goal
            target_y = f_width / 2
            distance_to_goal = math.hypot(self.x - target_x, self.y - target_y)
            in_opponent_half = self.x > f_length / 2

            if in_opponent_half and distance_to_goal > 200:
                dribble_power = 0.5
                avoid_angle = self.avoid_opponent_while_dribbling(ball, target_x, target_y)
                angle = avoid_angle if avoid_angle is not None else math.atan2(target_y - ball.y, target_x - ball.x)
                angle += math.radians(random.uniform(-10, 10))
                ball.velocity_x = math.cos(angle) * dribble_power
                ball.velocity_y = math.sin(angle) * dribble_power
                ball.last_movement_time = time.time()
            else:
                kick_power = 3 if distance_to_goal <= 200 else 2
                angle = math.atan2(target_y - ball.y, target_x - ball.x)
                angle += math.radians(random.uniform(-5, 5))
                ball.velocity_x = math.cos(angle) * kick_power
                ball.velocity_y = math.sin(angle) * kick_power
                ball.last_movement_time = time.time()

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        direction_x = self.x + math.cos(self.facing_angle) * self.radius
        direction_y = self.y + math.sin(self.facing_angle) * self.radius
        pygame.draw.line(screen, (255, 255, 255), (self.x, self.y), (direction_x, direction_y), 2)

        if self.player_type == 'attacker' and self.x > f_length / 2 and \
           math.hypot(self.x - f_length, self.y - f_width / 2) > 200:
            for p in self.players:
                if p.team != self.team and math.hypot(self.x - p.x, self.y - p.y) < 50:
                    pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius + 4, 2)
                    break

def main():
    pygame.init()
    screen = pygame.display.set_mode((f_length, f_width))
    pygame.display.set_caption("Two Static Defenders Dribbling Avoidance Test with Path")
    clock = pygame.time.Clock()

    # Initialize players and ball
    attacker = Player(500, 300, 'red', (255, 0, 0), 'attacker')
    defender1 = Player(540, 310, 'blue', (0, 0, 255), 'defender')
    defender2 = Player(580, 290, 'blue', (0, 0, 255), 'defender')  # Second defender
    ball = Ball(510, 305)
    players = [attacker, defender1, defender2]
    attacker.set_all_players(players)
    defender1.set_all_players(players)
    defender2.set_all_players(players)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        attacker.move(ball)
        # Defenders remain static
        ball.move()

        # Draw
        screen.fill((0, 200, 0))  # Green field
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, f_length, f_width), 2)
        pygame.draw.line(screen, (255, 255, 255), (f_length // 2, 0), (f_length // 2, f_width), 2)
        goal_y = f_width // 2
        pygame.draw.rect(screen, (255, 255, 255), (f_length - 60, goal_y - 130, 60, 260), 2)

        # Draw attacker's movement path
        if len(attacker.position_history) > 1:
            pygame.draw.lines(screen, (255, 0, 0), False, attacker.position_history, 2)

        for player in players:
            player.draw(screen)
        pygame.draw.circle(screen, (255, 255, 255), (int(ball.x), int(ball.y)), ball.radius)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()