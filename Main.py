from __future__ import division
import time
import pygame
import math
import decimal
import random
from operator import itemgetter
from decimal import getcontext, Decimal as d
_default_precision = getcontext().prec

from RPGCore import Movement, split_decimal_part
from RPGWorld import *

def quick_hash(x, y, offset=10):
    dx = hash(str(x) + str(y / 2))
    dy = hash(str(y * x / 2))
    num = int(0.5 * (dx + dy) * (dx + dy + 1)) % (offset * 2) - offset
    return num
    

class Player(object):
    """Class to store the player data."""

    def __init__(self, start=(0, 0, 0), bearing=0,
                 speed_max=1, speed_accel=3, speed_damp=4, 
                 turn_max=4, turn_accel=16, turn_damp=100000):
        
        self.loc = Movement(start)
        self.bearing = 0
        
        self.speed_max = speed_max
        self.speed_accel = d(speed_accel)
        self.speed_damp = speed_damp
        
        self.turn_max = turn_max
        self.turn_accel = turn_accel
        self.turn_damp = turn_damp
        
        self.turning = 0
        self.speed = [d(0) for i in range(3)]
        self.bearing = bearing
        self.rz = 0
        
        self.has_moved = False
        self.has_turned = True
        self.step(1)
    
    def _split_speed(self, speed):
        #Stop if max speed has been reached, around 10^306
        if str(speed) == 'inf':
            speed = 0
        return [d(i) * d(speed) for i in (self.rx, self.ry, self.rz)]
    
    def step(self, frame_time):
        
        if not self.has_turned:
            turn_damp = self.turn_damp * frame_time
            if self.turning:
                if self.turning < 0:
                    self.turning = min(0, self.turning + turn_damp)
                else:
                    self.turning = max(0, self.turning - turn_damp)
                self.has_turned = True
        
        if self.has_turned:
            self.bearing += self.turning * frame_time
            self.bearing = float(self.bearing) % (2 * math.pi)
            self.rx = math.sin(self.bearing)
            self.ry = math.cos(self.bearing)
            self.has_turned = False
        
    
        frame_time = d(frame_time)
        if not self.has_moved:
            speed_damp = self.speed_damp * frame_time
            for i, speed in enumerate(self.speed):
                if not speed:
                    continue
                elif speed < 0:
                    self.speed[i] = min(0, speed + speed_damp)
                else:
                    self.speed[i] = max(0, speed - speed_damp)
                self.has_moved = True
                    
        if self.has_moved:
            self.loc.move([i * frame_time for i in self.speed])
            self.has_moved = False
        
        
    def coordinates(self, update=None):
        if update:
            self.loc = Movement(*update)
        return self.loc._convert_to_world()
        
    def turn(self, amount=None, frame_time=1, backwards=False):
        if amount is None:
            amount = self.turn_accel
        if backwards:
            amount *= -1
        self.turning += amount * frame_time
        self.limit_turn()
        self.has_turned = True
    
    def move(self, amount=None, frame_time=1, backwards=False):
        if amount is None:
            amount = self.speed_accel
        if backwards:
            amount *= -1
        speed_increment = self._split_speed(amount)
        
        #Fix to stop precision running out on super fast speeds
        current_precision = getcontext().prec
        str_speed = str(speed_increment[1])
        len_speed = len(str_speed.split('.')[0])
        if 'E+' in str_speed:
            getcontext().prec = int(str_speed.split('E+')[1])
        elif len_speed > current_precision:
            getcontext().prec = len_speed
        elif current_precision != _default_precision and len_speed < _default_precision:
            getcontext().prec = _default_precision
            
        self.speed = [i + j * d(frame_time) for i, j in zip(self.speed, speed_increment)]
        self.limit_speed()
        self.has_moved = True
    
    def limit_turn(self):
        if self.turning < 0:
            self.turning = max(-self.turn_max, self.turning)
        else:
            self.turning = min(self.turn_max, self.turning)
    
    def limit_speed(self):
        if self.speed_max is None:
            return
        total_speed = d(pow(sum(pow(i, 2) for i in self.speed), d('0.5')))
        speed_max = d(self.speed_max)
        if total_speed > speed_max:
            multiplier = speed_max / total_speed
            self.speed = [i * multiplier for i in self.speed]
            

class MainGame(object):

    WIDTH = 1280
    HEIGHT = 720
    DEFAULT_TILE = WATER
    
    def _game_core(self):
        
        
        move_forward = self._keys[pygame.K_w]
        move_backward = self._keys[pygame.K_s]
        turn_left = self._keys[pygame.K_a]
        turn_right = self._keys[pygame.K_d]
        cam_up = self._keys[pygame.K_UP]
        cam_down = self._keys[pygame.K_DOWN]
        cam_left = self._keys[pygame.K_LEFT]
        cam_right = self._keys[pygame.K_RIGHT]
        
        if move_forward:
            self.player.move(frame_time=self._frame_time)
        if move_backward:
            self.player.move(frame_time=self._frame_time, backwards=True)
        if turn_left:
            self.player.turn(frame_time=self._frame_time)
        if turn_right:
            self.player.turn(frame_time=self._frame_time, backwards=True)
        
        n = 1
        if self._keys[pygame.K_RSHIFT]:
         n *= 100000000
        if cam_up:
            #self.camera[1] -= n
            self.camera._move(1, -n)
        if cam_down:
            #self.camera[1] += n
            self.camera._move(1, n)
        if cam_left:
            #self.camera[0] -= n
            self.camera._move(0, -n)
        if cam_right:
            #self.camera[0] += n
            self.camera._move(0, n)
        if any((cam_up, cam_down, cam_left, cam_right)):
            self.recalculate()
        
        
        self._draw_tiles()
        
        #print self.player.coordinates(), self.player.speed, self.player.bearing, self.player.turning
        #self.player.speed_accel *= d('1.01')
            
        self.player.step(self._frame_time)
        
        
    
    def _draw_tiles(self):
        
        self._redraw = True
        
        #cam_reversed = [-i for i in self.camera]
        for x in self.x_range:
            for y in self.y_range:
                coordinate = (x, y)
                try:
                    colour = TILECOLOURS[tilemap[coordinate]]
                except:
                    colour = TILECOLOURS[self.DEFAULT_TILE]
                    
                sx, sy = self.block_locations[coordinate]
                colour_offset = self.block_hashes[coordinate]
                colour = [min(255, max(0, c + colour_offset)) for c in colour]
                
                pygame.draw.rect(self.screen, colour, (sx * self.tilesize, sy * self.tilesize, self.tilesize, self.tilesize)) 

    
    def recalculate(self):
        
        #self.tilesize = max(self.min_tilesize, self.tilesize)
        #num_tiles_x = int(self.WIDTH / self.tilesize)
        
    
        cam_loc = [int(i.split('.')[0]) for i in self.camera._convert_to_world()]
        self.x_min = cam_loc[0] - 1
        self.y_min = cam_loc[1] - 1
        self.x_max = cam_loc[0] + int(self.WIDTH / self.tilesize) + 1
        self.y_max = cam_loc[1] + int(self.HEIGHT / self.tilesize) + 1
        
        #To check the culling
        if False:
            self.x_min += 2
            self.x_max -= 2
            self.y_min += 2
            self.y_max -= 2
            
        self.x_range = range(self.x_min, self.x_max)
        self.y_range = range(self.y_min, self.y_max)
        
        cx, cy = [-int(i.split('.')[0]) for i in self.camera._convert_to_world()]
        
        
        #Delete the keys that have gone off screen
        del_keys = []
        for key in self.block_locations:
            if not self.x_min < key[0] < self.x_max or not self.y_min < key[1] < self.y_max:
                del_keys.append(key)
            elif key not in self.block_hashes:
                self.block_hashes[coordinate] = quick_hash(*coordinate, offset=10)
        for key in del_keys:
            del self.block_locations[key]
            del self.block_hashes[key]
        
        #Find out the difference since the last frame
        old_block_locations = self.block_locations.copy()
        try:
            x_diff = self.x_min_o - self.x_min
            y_diff = self.y_min_o - self.y_min
        except (NameError, AttributeError):
            self.x_min_o = self.x_min
            self.y_min_o = self.y_min
            x_diff = y_diff = 0
        
        #Rebuild the new list of blocks
        for x in self.x_range:
            for y in self.y_range:
                coordinate = (x, y)
                old_coordinate = (x + x_diff, y + y_diff)
                try:
                    self.block_locations[coordinate] = old_block_locations[old_coordinate]
                    self.block_hashes[coordinate]
                except KeyError:
                    self.block_locations[coordinate] = (x + cx, y + cy)
                    self.block_hashes[coordinate] = quick_hash(*coordinate, offset=10)
                '''
                if coordinate not in self.block_locations:
                    self.block_locations[coordinate] = (x + cx, y + cy, quick_hash(*coordinate, offset=10))
                else:
                    try:
                        raise KeyError()
                        self.block_locations[coordinate] = old_block_locations[(x + x_diff, y + y_diff)]
                    except KeyError:
                        self.block_locations[coordinate] = (x + cx, y + cy, quick_hash(*coordinate, offset=10))
        
                '''
        self.x_min_o = self.x_min
        self.y_min_o = self.y_min
        
    
    def _update_window(self):
        self.block_locations = {}
        self.block_hashes = {}
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE)
        self.recalculate()
    
    def play(self):
    
        #Initialise screen
        pygame.init()
        self.camera = Movement((10**1, 0))
        pygame.display.set_caption('Basic RPG')
        self.clock = pygame.time.Clock()
        self.tilesize = TILESIZE
        
        self.max_tiles = (50, 10000)
        
        self._update_window()
        
        #Fill background
        self.screen.fill((255, 255, 255))
        
        #Initialise player and movement
        speed_mult = 100
        self.player = Player(speed_max=None,#1 * speed_mult, 
                             speed_accel=3 * speed_mult,  
                             speed_damp=0,#4 * speed_mult, 
                             bearing=0)
        
        time_current = time_last = time.time()
        self.num_frames = 0
        
        while True:
            self.num_frames += 1
            time_current = time.time()
            self._frame_time = time_current - time_last
            self._events = pygame.event.get()
            self._keys = pygame.key.get_pressed()
            self._redraw = False
            
            if self._keys[pygame.K_ESCAPE]:
                pygame.quit()
            for event in self._events:
            
                if event.type == pygame.QUIT:
                    return
                    
                elif event.type == pygame.VIDEORESIZE:
                
                    self.WIDTH, self.HEIGHT = event.dict['size']
                    self._update_window()
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    scroll_speed = self.tilesize // 10 + 1
                    if event.button == 4:
                        self.tilesize += scroll_speed
                        self.recalculate()
                    if event.button == 5:
                        self.tilesize -= scroll_speed
                        self.recalculate()
            
            self._game_core()
            #if not self.num_frames % 1000:
            #    print self.player.loc.raw[1], self.player.speed[1]
            
            #c = [int(round(float(i))) for i in self.player.coordinates()]
            #self.screen.set_at((c[0], c[1]), (0, 0, 0))
            if self._redraw:
                pygame.display.flip()
                self.screen.fill((255, 255, 255))
                #self._draw_tiles()
                
            self.clock.tick(60)
            pygame.display.set_caption(str(self.clock.get_fps()))
            time_last = time_current
            
MainGame().play()
