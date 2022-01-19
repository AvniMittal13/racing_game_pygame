from operator import and_
import torch
import random
import numpy as np
from collections import deque
from main import PlayerCarAI, left_x_limit, right_x_limit
from model import Linear_QNet, QTrainer
from plot_it import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.01

class Agent:

    def __init__(self, game):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.model = Linear_QNet(3+(3*int(360/game.angle)), 256, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)


    def get_state(self, game):
        dir_l = game.direction == [0,1,0]
        dir_r = game.direction == [0,0,1]
        dir_u = game.direction == [1,0,0]

        state = [
            # Move direction

            dir_l,
            dir_r,
            dir_u,
            ]

        # now getting all points on circle around agent car
        for counter,pt in enumerate(game.pts1):
            angle = 30*(counter)
            if angle<90:
                state.append(dir_r and game.get_state(*pt))
            elif angle==0:
                state.append(dir_u and game.get_state(*pt))
            elif angle>270:
                state.append(dir_l and game.get_state(*pt))
            else:
                state.append(game.get_state(*pt))

        for counter,pt in enumerate(game.pts2):
            angle = 30*(counter)
            if angle<90:
                state.append(dir_r and game.get_state(*pt))
            elif angle==0:
                state.append(dir_u and game.get_state(*pt))
            elif angle>270:
                state.append(dir_l and game.get_state(*pt))
            else:
                state.append(game.get_state(*pt))

        for counter,pt in enumerate(game.pts3):
            angle = 30*(counter)
            if angle<90:
                state.append(dir_r and game.get_state(*pt))
            elif angle==0:
                state.append(dir_u and game.get_state(*pt))
            elif angle>270:
                state.append(dir_l and game.get_state(*pt))
            else:
                state.append(game.get_state(*pt))

            
        
        



        # point_u = (game.x, game.y-199)
        # point_l = (game.x-100, game.y)
        # point_r = (game.x+100, game.y)
        # point_ul=(game.x-100,game.y-199)
        # point_ur=(game.x+100,game.y-199)
        # point_bl=(left_x_limit,game.y)
        # point_br=(right_x_limit,game.y)

        
        
        # dir_l = game.direction == [0,1,0]
        # dir_r = game.direction == [0,0,1]
        # dir_u = game.direction == [1,0,0]

        # state = [
        #     # Danger straight
        #     (dir_u and game.get_state(*point_u)),

        #     # Danger right
        #     (dir_r and game.get_state(*point_r)),

        #     # Danger left 
        #     (dir_l and game.get_state(*point_l)),

        #     # Danger upleft
        #     (dir_l and game.get_state(*point_ul)),

        #     # Danger upright
        #     (dir_r and game.get_state(*point_ur)),

        #     # Danger border right
        #     (dir_r and game.get_state(*point_br)),

        #     # Danger border left
        #     (dir_l and game.get_state(*point_bl)),
            
        #     # Move direction
        #     dir_l,
        #     dir_r,
        #     dir_u,
        #     ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        #for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 80 - self.n_games
        final_move = [0,0,0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    game = PlayerCarAI()
    agent = Agent(game)
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.player_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()