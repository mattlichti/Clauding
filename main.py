import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Game constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLUE = (50, 50, 200)

# Set up display
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)


def get_level_obstacles(level):
    """Return obstacle positions for each level."""
    obstacles = set()

    if level == 1:
        # No obstacles
        pass

    elif level == 2:
        # Center horizontal bar (offset from center so snake can spawn)
        for x in range(6, 14):
            obstacles.add((x, 7))

    elif level == 3:
        # Two vertical bars
        for y in range(5, 15):
            obstacles.add((5, y))
            obstacles.add((14, y))

    elif level == 4:
        # Four corner blocks
        for x in range(3, 6):
            for y in range(3, 6):
                obstacles.add((x, y))
                obstacles.add((GRID_SIZE - 1 - x, y))
                obstacles.add((x, GRID_SIZE - 1 - y))
                obstacles.add((GRID_SIZE - 1 - x, GRID_SIZE - 1 - y))

    elif level >= 5:
        # Cross pattern
        for i in range(4, 16):
            obstacles.add((10, i))
            obstacles.add((i, 10))
        # Remove center to allow passage
        obstacles.discard((10, 10))
        obstacles.discard((9, 10))
        obstacles.discard((11, 10))
        obstacles.discard((10, 9))
        obstacles.discard((10, 11))

    return obstacles


def get_random_food(snake, obstacles):
    """Get a random position for food that's not on the snake or obstacles."""
    while True:
        pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
        if pos not in snake and pos not in obstacles:
            return pos


def draw_grid():
    """Draw the grid lines."""
    for x in range(0, WINDOW_SIZE, CELL_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, WINDOW_SIZE))
    for y in range(0, WINDOW_SIZE, CELL_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (0, y), (WINDOW_SIZE, y))


def draw_snake(snake):
    """Draw the snake."""
    for i, segment in enumerate(snake):
        x, y = segment
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        color = GREEN if i == 0 else DARK_GREEN
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)


def draw_food(food):
    """Draw the food."""
    x, y = food
    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, RED, rect)
    pygame.draw.rect(screen, BLACK, rect, 1)


def draw_obstacles(obstacles):
    """Draw the obstacles."""
    for obs in obstacles:
        x, y = obs
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, BLUE, rect, 2)


def draw_hud(score, level, lives):
    """Draw the score, level, and lives."""
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    lives_text = font.render(f"Lives: {lives}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (WINDOW_SIZE // 2 - lives_text.get_width() // 2, 10))
    screen.blit(level_text, (WINDOW_SIZE - level_text.get_width() - 10, 10))


def draw_level_transition(level):
    """Draw level transition screen."""
    screen.fill(BLACK)
    level_text = big_font.render(f"Level {level}", True, WHITE)
    start_text = font.render("Press SPACE to start", True, WHITE)
    screen.blit(level_text, (WINDOW_SIZE // 2 - level_text.get_width() // 2, WINDOW_SIZE // 2 - 50))
    screen.blit(start_text, (WINDOW_SIZE // 2 - start_text.get_width() // 2, WINDOW_SIZE // 2 + 30))
    pygame.display.flip()


def draw_game_over(score, level):
    """Draw game over screen."""
    screen.fill(BLACK)
    game_over_text = big_font.render("GAME OVER", True, RED)
    score_text = font.render(f"Final Score: {score}  (Level {level})", True, WHITE)
    restart_text = font.render("Press SPACE to restart or Q to quit", True, WHITE)

    screen.blit(game_over_text, (WINDOW_SIZE // 2 - game_over_text.get_width() // 2, WINDOW_SIZE // 2 - 60))
    screen.blit(score_text, (WINDOW_SIZE // 2 - score_text.get_width() // 2, WINDOW_SIZE // 2 + 20))
    screen.blit(restart_text, (WINDOW_SIZE // 2 - restart_text.get_width() // 2, WINDOW_SIZE // 2 + 70))
    pygame.display.flip()


def main():
    level = 1
    score = 0
    level_score = 0  # Score within current level
    points_per_level = 50  # Points needed to advance
    lives = 3

    obstacles = get_level_obstacles(level)
    snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
    direction = (1, 0)
    food = get_random_food(snake, obstacles)

    game_over = False
    level_transition = True  # Start with level intro

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_SPACE:
                        # Full restart
                        level = 1
                        score = 0
                        level_score = 0
                        lives = 3
                        obstacles = get_level_obstacles(level)
                        snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
                        direction = (1, 0)
                        food = get_random_food(snake, obstacles)
                        game_over = False
                        level_transition = True
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                elif level_transition:
                    if event.key == pygame.K_SPACE:
                        level_transition = False
                else:
                    # Change direction (prevent 180-degree turns)
                    if event.key == pygame.K_UP and direction != (0, 1):
                        direction = (0, -1)
                    elif event.key == pygame.K_DOWN and direction != (0, -1):
                        direction = (0, 1)
                    elif event.key == pygame.K_LEFT and direction != (1, 0):
                        direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                        direction = (1, 0)

        if game_over:
            draw_game_over(score, level)
            clock.tick(60)
            continue

        if level_transition:
            draw_level_transition(level)
            clock.tick(60)
            continue

        # Move snake
        head_x, head_y = snake[0]
        new_head = (head_x + direction[0], head_y + direction[1])

        # Check wall collision
        hit = False
        if (new_head[0] < 0 or new_head[0] >= GRID_SIZE or
            new_head[1] < 0 or new_head[1] >= GRID_SIZE):
            hit = True

        # Check obstacle collision
        if new_head in obstacles:
            hit = True

        # Check self collision
        if new_head in snake:
            hit = True

        if hit:
            lives -= 1
            if lives <= 0:
                game_over = True
            else:
                # Respawn snake, keep score and level
                snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
                direction = (1, 0)
                food = get_random_food(snake, obstacles)
            continue

        # Add new head
        snake.insert(0, new_head)

        # Check food collision
        if new_head == food:
            score += 10
            level_score += 10

            # Check for level up
            if level_score >= points_per_level and level < 5:
                level += 1
                level_score = 0
                obstacles = get_level_obstacles(level)
                # Reset snake position for new level
                snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
                direction = (1, 0)
                food = get_random_food(snake, obstacles)
                level_transition = True
            else:
                food = get_random_food(snake, obstacles)
        else:
            snake.pop()

        # Draw everything
        screen.fill(BLACK)
        draw_grid()
        draw_obstacles(obstacles)
        draw_snake(snake)
        draw_food(food)
        draw_hud(score, level, lives)
        pygame.display.flip()

        # Control game speed (slightly faster at higher levels)
        speed = 10 + (level - 1) * 2
        clock.tick(speed)


if __name__ == "__main__":
    main()
