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

# Set up display
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)


def get_random_food(snake):
    """Get a random position for food that's not on the snake."""
    while True:
        pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
        if pos not in snake:
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


def draw_score(score):
    """Draw the score."""
    text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(text, (10, 10))


def draw_game_over(score):
    """Draw game over screen."""
    screen.fill(BLACK)
    game_over_text = font.render("GAME OVER", True, RED)
    score_text = font.render(f"Final Score: {score}", True, WHITE)
    restart_text = font.render("Press SPACE to restart or Q to quit", True, WHITE)

    screen.blit(game_over_text, (WINDOW_SIZE // 2 - game_over_text.get_width() // 2, WINDOW_SIZE // 2 - 60))
    screen.blit(score_text, (WINDOW_SIZE // 2 - score_text.get_width() // 2, WINDOW_SIZE // 2))
    screen.blit(restart_text, (WINDOW_SIZE // 2 - restart_text.get_width() // 2, WINDOW_SIZE // 2 + 60))
    pygame.display.flip()


def main():
    # Initial snake position (middle of screen, 3 segments)
    snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
    direction = (1, 0)  # Moving right
    food = get_random_food(snake)
    score = 0
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_SPACE:
                        # Restart game
                        snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
                        direction = (1, 0)
                        food = get_random_food(snake)
                        score = 0
                        game_over = False
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
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
            draw_game_over(score)
            clock.tick(60)
            continue

        # Move snake
        head_x, head_y = snake[0]
        new_head = (head_x + direction[0], head_y + direction[1])

        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= GRID_SIZE or
            new_head[1] < 0 or new_head[1] >= GRID_SIZE):
            game_over = True
            continue

        # Check self collision
        if new_head in snake:
            game_over = True
            continue

        # Add new head
        snake.insert(0, new_head)

        # Check food collision
        if new_head == food:
            score += 10
            food = get_random_food(snake)
        else:
            snake.pop()  # Remove tail if no food eaten

        # Draw everything
        screen.fill(BLACK)
        draw_grid()
        draw_snake(snake)
        draw_food(food)
        draw_score(score)
        pygame.display.flip()

        # Control game speed
        clock.tick(10)


if __name__ == "__main__":
    main()
