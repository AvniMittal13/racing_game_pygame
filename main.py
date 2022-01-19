import pygame
import time
import math
import random
import os
import numpy as np
from collections import deque

pygame.init()
font1 = pygame.font.Font('freesansbold.ttf', 32)
pygame.mixer.init()
MAX_MEMORY = 100_000

from pygame.constants import HIDDEN
from utils import scale_image, blit_rotate_center

all_vehicles=os.listdir('images')
for val in ['crash.png', 'grass.jpg', 'main_agent.png', 'main_agent2.png','track.png','Thumbs.db','speedometer.png']:
    all_vehicles.remove(val)
# print(all_vehicles)

GRASS = scale_image(pygame.image.load("images/grass.jpg"), 1.6)
TRACK = scale_image(pygame.image.load("images/track.png"), 1.6)
CRASH = scale_image(pygame.image.load("images/crash.png"),0.5)
SPEEDOMETER=scale_image(pygame.image.load("images/speedometer.png"), 0.45)

#TRACK_BORDER = scale_image(pygame.image.load("imgs/track-border.png"), 0.9)

RED_CAR = scale_image(pygame.image.load("images/main_agent2.png"), 0.55)
GREEN_CAR = scale_image(pygame.image.load("images/police.png"), 0.55)
TRUCK=scale_image(pygame.image.load("images/truck.png"), 0.55)

# WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIDTH, HEIGHT = GRASS.get_width(), GRASS.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

FPS = 60

# setting the path limits
left_x_limit=260
right_x_limit=WIDTH-365

x_random=np.arange(left_x_limit,right_x_limit,50)    

class PlayerCarAI():
    def __init__(self, max_vel=20, angle_deg = 18):
        # player car attributes
        self.img = RED_CAR
        self.initial_vel=max_vel
        self.max_vel = max_vel
        self.vel = 5
        self.x, self.y = (5*HEIGHT/6, WIDTH-450)
        self.acceleration = 0.07
        self.score=0
        self.game_over=False
        self.direction=[0,0,0]
        self.angle = angle_deg
        self.inner_rad = int(WIDTH/6)
        self.outer_rad = int(WIDTH/3)
        self.mid_rad = int(WIDTH/4)

        # getting starting points for inner and outer circle
        self.pts1=self.get_pts(self.inner_rad)
        self.pts3=self.get_pts(self.mid_rad)
        self.pts2=self.get_pts(self.outer_rad)

        # 2 obstacles -> attributes start
        x_random=np.arange(left_x_limit,right_x_limit,50)
        # list1=x_random.tolist()
        # list1.remove(list1[0])
        # x_random2=random.choices(list1,k=1)
        x_choices = set(x_random)
        x_blocks = random.sample(x_choices, 2)

        self.x1=x_blocks[0]
        self.x2=x_blocks[1]
        self.y1=-100
        self.y2=-120
        self.v1=5
        self.v2=5
        self.min_velocity=5
        self.acceleration = 0.1

        self.image1=GREEN_CAR
        self.image2=TRUCK
        self.vehicle_number=[]

        self.dodged = 0
        self.rewards=deque(maxlen=MAX_MEMORY)
        self.rewards.append(0)

        # surroundings movement
        self.movement_in_y=0

    def get_pts(self ,rad):
        center = (self.x + 20 ,self.y + 50)
        angle = 0
        radius = rad
        pts = []
        for i in range(int(360/self.angle)):
            vec = pygame.math.Vector2(0, -radius).rotate(angle)
            pt_x, pt_y = center[0] + vec.x, center[1] + vec.y

            if (pt_x > right_x_limit):
                pt_x = right_x_limit+40
            elif(pt_x < left_x_limit):
                pt_x = left_x_limit
            
            pts.append((pt_x,pt_y))
            angle += self.angle     
            if angle >= 360:
                angle = 0

        # for pt_x,pt_y in pts:
        #     pygame.draw.circle(WIN, (0, 0, 0), center, radius, 2)
        #     pygame.draw.line(WIN, (0, 0, 255), center, (pt_x, pt_y), 2)
        #     pygame.draw.line(WIN, (0, 0, 255), center, (center[0], center[1]-radius), 2)
        #     pygame.display.update()

        return pts

    def reset(self):
        self.__init__()

    def draw_player(self,win):
        win.blit(self.img,(self.x,self.y))
    
    # playet car methods->>>
    def move_forward(self):
        self.max_vel = self.initial_vel+(self.dodged//30)*2
        self.vel = min(self.vel + self.acceleration, self.max_vel)

    def movement(self,left=False,right=False):
        if left:
            horizontal = self.vel
            self.x -= horizontal
        elif right:
            horizontal = self.vel
            self.x += horizontal

        # check boundary (west)
        if self.x < left_x_limit:
           self.x = left_x_limit
        # check boundary (east)
        if self.x > right_x_limit:
           self.x = right_x_limit

    
    def player_step(self,action):

        # getting points from inner and outer circle
        self.pts1=self.get_pts(self.inner_rad)
        self.pts3=self.get_pts(self.mid_rad)
        self.pts2=self.get_pts(self.outer_rad)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        self.direction=action
        if action[1]:
            self.movement(left=True)
        elif action[2]:
            self.movement(right=True)

        # keep increasing speed
        self.move_forward()
        self.update()
        self.update_ui()

        # now updating the scorecard and reward
        reward=0
        
        if self.game_over:
            reward = -10
        else:  # give reward when dodged count increases
            reward = self.rewards.pop()

         # Score
        self.score=self.dodged

        #print("Reward: ",reward,",Score: ",self.score,",Game_Over: ",self.game_over)
        return reward, self.game_over,self.score


    # obstacles methods start->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update(self):
        flag=0
        self.v1=max(self.vel + self.acceleration, self.min_velocity)
        self.y1 = self.y1 + self.v1
        # for second obstacle
        self.v2=max(self.vel + self.acceleration, self.min_velocity)
        self.y2 = self.y2 + self.v2

        # choosing random coordinate and random cars
        x_random=np.arange(left_x_limit,right_x_limit,50)
        # list1=x_random.tolist()
        # list1.remove(list1[0])
        # x_random2=random.choices(list1,k=1)
        x_choices = set(x_random)
        x_blocks = random.sample(x_choices, 2)

        self.vehicle_number=random.sample(range(0,len(all_vehicles)-1),k=2)

       # check boundary (block) for obstacle 1
        if self.y1 > WIDTH:
            self.y1 = 0 - 10 # choosing randomly x coordinate
            if self.x2 == x_blocks[0]:
                possible_choices = [v for v in x_random if v != x_blocks[0]]
                x_blocks[0] = random.choice(possible_choices)

            self.x1 = x_blocks[0]
            #print(self.x,left_x_limit,right_x_limit-self.width)
            self.dodged = self.dodged + 2
            self.image1 = scale_image(pygame.image.load("images/"+all_vehicles[self.vehicle_number[0]]), 0.55)
            self.rewards.append(10)
            flag=1

        # check boundary (block) for obstacle 2
        if self.y2 > WIDTH:
            self.y2 = 0 - 20 # choosing randomly x coordinate
            if self.x1 == x_blocks[1]:
                possible_choices = [v for v in x_random if v != x_blocks[1]]
                x_blocks[1] = random.choice(possible_choices)
            self.x2 = x_blocks[1]
            #print(self.x,left_x_limit,right_x_limit-self.width)
            self.dodged = self.dodged + 2
            self.image2 = scale_image(pygame.image.load("images/"+all_vehicles[self.vehicle_number[1]]), 0.55)
            self.rewards.append(10)
            flag=1
            
        if(flag==0):
            self.rewards.append(0)
            

    def draw(self,win):
        win.blit(self.image1,(self.x1,self.y1))
        win.blit(self.image2,(self.x2,self.y2))

    def get_state(self,x,y):
        obstacle1_mask = pygame.mask.from_surface(self.image1)
        offset1 = (int(self.x1 - x), int(self.y1 - y))

        obstacle2_mask = pygame.mask.from_surface(self.image2)
        offset2 = (int(self.x2 - x), int(self.y2 - y))
        
        # mask of player car
        mask=pygame.mask.from_surface(self.img)

        # now finding point of intersection
        poi1 = mask.overlap(obstacle1_mask, offset1)
        poi2 = mask.overlap(obstacle2_mask, offset2)

        if poi1!=None or poi2!=None:
            return True
        
        return False

    def collison(self):
        obstacle1_mask = pygame.mask.from_surface(self.image1)
        offset1 = (int(self.x1 - self.x), int(self.y1 - self.y))

        obstacle2_mask = pygame.mask.from_surface(self.image2)
        offset2 = (int(self.x2 - self.x), int(self.y2 - self.y))
        
        # mask of player car
        mask=pygame.mask.from_surface(self.img)

        # now finding point of intersection
        poi1 = mask.overlap(obstacle1_mask, offset1)
        poi2 = mask.overlap(obstacle2_mask, offset2)
        if poi1 != None:
            sound=pygame.mixer.Sound("sounds/car-crash-sound-eefect.mp3")
            sound.set_volume(0.5)
            sound.play()
            text = font1.render('You crashed!',True,(0,0,0))
            text_width = text.get_width()
            text_height = text.get_height()
            x = int(WIDTH/2-text_width/2)
            y = int(HEIGHT/2-text_height/2)
            WIN.blit(text,(x,y))
            WIN.blit(CRASH,(self.x-100,self.y-100))
            pygame.display.update()
            time.sleep(1)
            return True

        # checking collision for second car
        if poi2 != None:
            sound=pygame.mixer.Sound("sounds/car-crash-sound-eefect.mp3")
            sound.set_volume(0.5)
            sound.play()
            text = font1.render('You crashed!',True,(0,0,0))
            text_width = text.get_width()
            text_height = text.get_height()
            x = int(WIDTH/2-text_width/2)
            y = int(HEIGHT/2-text_height/2)
            WIN.blit(text,(x,y))
            WIN.blit(CRASH,(self.x-100,self.y-100))
            pygame.display.update()
            time.sleep(1)
            return True
        
        return False
        
    def score_board(self):
        global font1
        text = font1.render('Dodged: ' + str(self.dodged),True,(0,0,0))
        WIN.blit(text,(0,0)) 

    def speedometer(self):
        global font1
        text = font1.render(str(round(self.vel,1))+"  KMPH",True,(0,0,0))
        WIN.blit(SPEEDOMETER,(0,155))
        WIN.blit(text,(60,145))

    def update_ui(self):
        clock.tick(FPS)

        # displaying grass road and car
        WIN.blit(GRASS,(0,self.movement_in_y))
        WIN.blit(GRASS,(0,self.movement_in_y-GRASS.get_height()))

        # to move and display the road
        WIN.blit(TRACK,(0,self.movement_in_y))
        WIN.blit(TRACK,(0,self.movement_in_y-TRACK.get_height()))

        self.movement_in_y+=self.vel

        if (TRACK.get_height()-int(self.movement_in_y))<=11:
            WIN.blit(GRASS,(0,self.movement_in_y-GRASS.get_height()))
            WIN.blit(TRACK,(0,self.movement_in_y-TRACK.get_height()))
            self.movement_in_y=0

        self.draw_player(WIN)
        self.draw(WIN)
        self.score_board()
        self.speedometer()

        if self.game_over:
            self.reset()

        if(self.collison()):
            self.game_over=True

        pygame.display.update()
        
        


clock = pygame.time.Clock()
# player_car = PlayerCarAI()



# for _ in range(50000000):
#     indx=np.random.randint(0,3)
#     action=[0,0,0]
#     action[indx]=1
#     player_car.player_step(action)


# pygame.quit()
