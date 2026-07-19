import os
import sys
import random
from collections import deque

import torch
import torch.nn as nn

from environment.environment import SnakeGame, Direction


GRID = (32, 24)
EPISODES = 1200
GAMMA = 0.9
LR = 0.001
BATCH_SIZE = 64
MEMORY_SIZE = 100_000
HIDDEN = 256
TARGET_UPDATE = 1000

EPSILON = 1.0
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.995

MODEL_PATH = os.path.join(os.path.dirname(__file__), "dqn_model.pth")
directions = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
device = torch.device("mps" if torch.mps.is_available() else "cpu")


class DQN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(11, HIDDEN),
            nn.ReLU(),
            nn.Linear(HIDDEN, 3),
        )

    def forward(self, x):
        return self.net(x)


model = DQN().to(device)
target_model = DQN().to(device)
target_model.load_state_dict(model.state_dict())
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
loss_fn = nn.MSELoss()
memory = deque(maxlen=MEMORY_SIZE)


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


def select_action(state):
    """ Prob. epsilon to explore actions, otherwise to exploit the highest action"""
    if random.random() < EPSILON:
        return random.randint(0, 2)
    state_t = torch.tensor(state, dtype=torch.float, device=device)
    with torch.no_grad():
        q_values = model(state_t)
    return int(torch.argmax(q_values).item())


def train_step():
    if len(memory) < BATCH_SIZE:
        return
    batch = random.sample(memory, BATCH_SIZE)
    states, actions, rewards, next_states, dones = zip(*batch)

    states = torch.tensor(states, dtype=torch.float, device=device)
    actions = torch.tensor(actions, dtype=torch.long, device=device).unsqueeze(1)
    rewards = torch.tensor(rewards, dtype=torch.float, device=device)
    next_states = torch.tensor(next_states, dtype=torch.float, device=device)
    dones = torch.tensor(dones, dtype=torch.float, device=device)

    pred = model(states).gather(1, actions).squeeze(1)

    with torch.no_grad():
        next_q = target_model(next_states).max(1)[0]
        target = rewards + GAMMA * next_q * (1 - dones)

    loss = loss_fn(pred, target)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()


def train():
    global EPSILON
    game = SnakeGame(dim=GRID, speed=10_000)
    game._update_ui = lambda: None

    scores = deque(maxlen=50)
    steps = 0

    for episode in range(EPISODES):
        game.reset()
        state = get_state(game)
        done = False
        while not done:
            action = select_action(state)
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

            next_state = get_state(game)
            memory.append((state, action, reward, next_state, float(done)))
            state = next_state

            train_step()

            steps += 1
            if steps % TARGET_UPDATE == 0:
                target_model.load_state_dict(model.state_dict())

        scores.append(score)
        if EPSILON > EPSILON_MIN:
            EPSILON = EPSILON * EPSILON_DECAY

        if (episode + 1) % 20 == 0:
            avg = sum(scores) / len(scores)
            print(f"episode {episode + 1:4d} | score {score:3d} | "
                  f"avg50 {avg:5.2f} | epsilon {EPSILON:.3f}")

    torch.save(model.state_dict(), MODEL_PATH)
    print("training done, saved model to", MODEL_PATH)


def play():
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    game = SnakeGame(dim=GRID, speed=10)
    while True:
        game.reset()
        done = False
        while not done:
            state = get_state(game)
            state_t = torch.tensor(state, dtype=torch.float, device=device)
            with torch.no_grad():
                action = int(torch.argmax(model(state_t)).item())
            status, done, score = game.play_step(get_direction(game.direction, action))
        print("game over, score", score)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        play()
    else:
        train()
        play()
