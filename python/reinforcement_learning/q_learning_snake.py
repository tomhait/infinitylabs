import os
import sys
import random
import pickle

from environment.environment import SnakeGame, Direction


GRID = (10, 10)
EPISODES = 3000
ALPHA = 0.1
GAMMA = 0.9
EPSILON = 1.0
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.995

Q_PATH = os.path.join(os.path.dirname(__file__), "q_table.pkl")
directions = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]

q_table = {}


def get_qs(state):
    if state not in q_table:
        q_table[state] = [0.0, 0.0, 0.0]
    return q_table[state]


def get_direction(current, action):
    """action: 0 = go straight, 1 = turn right, 2 = turn left"""
    i = directions.index(current)
    if action == 0:
        return directions[i]
    elif action == 1:
        return directions[(i + 1) % 4]
    else:
        return directions[(i - 1) % 4]


def move_point(game, point, direction):
    """where the head would be after moving"""
    x = point.x
    y = point.y
    if direction == Direction.RIGHT:
        x = x + 1
    elif direction == Direction.LEFT:
        x = x - 1
    elif direction == Direction.DOWN:
        y = y + 1
    elif direction == Direction.UP:
        y = y - 1
    return (x % game.w, y % game.h)


def is_danger(game, direction):
    """checks whether moving a given direction would hit the snake's own body"""
    body = game.snake[:-1]
    point = move_point(game, game.head, direction)
    return 1 if point in body else 0


def get_state(game):
    """ 3 danger bits for each action
        4 direction bits
        4 food bits - is it up, down, left or right
    """
    head = game.head
    d = game.direction

    straight = get_direction(d, 0)
    right = get_direction(d, 1)
    left = get_direction(d, 2)

    state = (
        is_danger(game, straight),
        is_danger(game, right),
        is_danger(game, left),
        1 if d == Direction.LEFT else 0,
        1 if d == Direction.RIGHT else 0,
        1 if d == Direction.UP else 0,
        1 if d == Direction.DOWN else 0,
        1 if game.food.x < head.x else 0,
        1 if game.food.x > head.x else 0,
        1 if game.food.y < head.y else 0,
        1 if game.food.y > head.y else 0,
    )
    return state


def get_distance(game):
    return abs(game.head.x - game.food.x) + abs(game.head.y - game.food.y)


def choose_action(state):
    """ Prob. epsilon to explore actions, otherwise to exploit the highest action"""
    if random.random() < EPSILON:
        return random.randint(0, 2)
    qs = get_qs(state)
    return qs.index(max(qs))


def train():
    global EPSILON
    game = SnakeGame(dim=GRID, speed=1000)

    for episode in range(EPISODES):
        game.reset()
        done = False
        while not done:
            state = get_state(game)
            action = choose_action(state)
            direction = get_direction(game.direction, action)

            old_distance = get_distance(game)
            status, done, score = game.play_step(direction)

            if status == SnakeGame.Status.EAT:
                reward = 10
            elif status == SnakeGame.Status.COLLISION or status == SnakeGame.Status.TIME_OUT:
                reward = -10
            elif get_distance(game) < old_distance:
                reward = 1
            else:
                reward = -1

            old_q = get_qs(state)[action]
            if done:
                new_q = reward
            else:
                next_state = get_state(game)
                new_q = reward + GAMMA * max(get_qs(next_state))
            get_qs(state)[action] = old_q + ALPHA * (new_q - old_q)

        if EPSILON > EPSILON_MIN:
            EPSILON = EPSILON * EPSILON_DECAY

        if (episode + 1) % 200 == 0:
            print("episode", episode + 1, "score", score, "epsilon", round(EPSILON, 3))

    f = open(Q_PATH, "wb")
    pickle.dump(q_table, f)
    f.close()
    print("training done, learned", len(q_table), "states")


def play():
    f = open(Q_PATH, "rb")
    q_table.update(pickle.load(f))
    f.close()

    game = SnakeGame(dim=GRID, speed=8)
    while True:
        game.reset()
        done = False
        while not done:
            state = get_state(game)
            qs = get_qs(state)
            action = qs.index(max(qs))
            status, done, score = game.play_step(get_direction(game.direction, action))
        print("game over, score", score)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        play()
    else:
        train()
        play()
