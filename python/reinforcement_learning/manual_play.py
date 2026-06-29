import pygame

from environment.environment import SnakeGame, Direction

KEY_TO_DIRECTION = {
    pygame.K_UP: Direction.UP,
    pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_d: Direction.RIGHT,
}

OPPOSITE = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


BASE_SPEED = 10
SPEED_STEP = 1
MAX_SPEED = 40


def play():
    game = SnakeGame(speed=BASE_SPEED)
    while True:
        game.reset()
        game.speed = BASE_SPEED
        direction = game.direction
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                    new_direction = KEY_TO_DIRECTION.get(event.key)
                    if new_direction is not None and new_direction != OPPOSITE[direction]:
                        direction = new_direction

            status, done, score = game.play_step(direction)

            if status == SnakeGame.Status.EAT:
                game.speed = min(game.speed + SPEED_STEP, MAX_SPEED)

        print(f"Game over - {status.name}, score: {score}")


if __name__ == "__main__":
    play()
    # game = SnakeGame(speed=BASE_SPEED)