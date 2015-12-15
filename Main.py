from __future__ import division
import time
import pygame
import math
import decimal
import random
from operator import itemgetter
from decimal import getcontext, Decimal as d
_default_precision = getcontext().prec

from DKWorld import *
from DKCollection import *
from FrameLimit import GameTime, GameTimeLoop

def quick_hash(x, y, offset=10):
    dx = hash(str(x // 2) + str(y))
    dy = hash(str((y * x) // 2))
    num = int(0.5 * (dx + dy) * (dx + dy + 1)) % (offset * 2) - offset
    return num

def split_num(n):
    return (int(n), remove_int(n))
    
def remove_int(n):
    if n > 0:
        return n % 1
    try:
        n_decimal = str(n).split('.')[1]
        return float('-0.' + n_decimal)
    except IndexError:
        return 0.0
        
class Camera(object):
    def __init__(self, x=0, y=0, speed=100):
        self.x_int, self.x_float = split_num(x)
        self.y_int, self.y_float = split_num(y)
        self.speed = speed
    
    def _formatstr(self, n_int, n_float):
        if n_int < 0:
            n_str = '-'[n_int != -1:] + str(n_int + 1) + '.' + str(1 - n_float)[2:]
        else:
            n_str = str(n_int) + '.' + str(n_float)[2:]
        return n_str
    
    def __str__(self):
        return str((self._formatstr(self.x_int, self.x_float), 
                    self._formatstr(self.y_int, self.y_float))).replace("'", "")
        
    def move(self, x=0, y=0, multiplier=1):
        if x:
            x_int, x_float = split_num(x * self.speed * multiplier)
            self.x_int += x_int
            self.x_float += x_float
                
        if y:
            y_int, y_float = split_num(y * self.speed * multiplier)
            self.y_int += y_int
            self.y_float += y_float
        
        self.overflow()
    
    def overflow(self):
        i = 1 if self.x_float >= 1 else -1
        while not 0 <= self.x_float < 1:
            self.x_float -= i
            self.x_int += i
        i = 1 if self.y_float >= 1 else -1
        while not 0 <= self.y_float < 1:
            self.y_float -= i
            self.y_int += i
    
class MainGame(object):

    WIDTH = 1280
    HEIGHT = 720
    DEFAULT_TILE = WATER
    TILE_MAX_SIZE = 128
    TILE_MIN_SIZE = 16
    FPS = None
    TICKS = 120
    BLOCK_TAG = set()

    def recalculate(self):
        try:
            self.frame_data['Redraw'] = True
        except AttributeError:
            pass
        overflow = 1
        self.x_min = self.cam.x_int - overflow
        self.y_min = self.cam.y_int - overflow
        self.x_max = self.cam.x_int + int(self.WIDTH / self.tilesize) + overflow
        self.y_max = self.cam.y_int + int(self.HEIGHT / self.tilesize) + overflow
        
        
        self.screen_coordinates = [(x, y) 
                                   for x in range(self.x_min, self.x_max) 
                                   for y in range(self.y_min, self.y_max)]
        
        
        #Delete the keys that have gone off screen
        del_keys = []
        for key in self.screen_block_data:
            if not self.x_min < key[0] < self.x_max or not self.y_min < key[1] < self.y_max:
                del_keys.append(key)
        for key in del_keys:
            del self.screen_block_data[key]
        
        
        #Rebuild the new list of blocks
        block_data_copy = self.screen_block_data.copy()
        for coordinate in self.screen_coordinates:
        
            block_type = get_tile(coordinate)
            tile_origin = ((coordinate[0] - self.cam.x_int) - self.cam.x_float, 
                           (coordinate[1] - self.cam.y_int) - self.cam.y_float)
            tile_location = tuple(i * self.tilesize for i in tile_origin)
            
            #Update existing point with new location
            if coordinate in self.screen_block_data and coordinate not in self.BLOCK_TAG:
                self.screen_block_data[coordinate][2] = tile_location
                continue
            
            #Generate new point info
            block_hash = quick_hash(*coordinate, offset=self.noise_level)
            main_colour = TILECOLOURS[block_type]
            if coordinate in self.BLOCK_TAG:
                main_colour = (0, 0, 0)
            block_colour = [min(255, max(0, c + block_hash)) for c in main_colour]
            self.screen_block_data[coordinate] = [block_type, 
                                                  block_colour, 
                                                  tile_location]
        
    
    def setscreen(self):
        try:
            self.frame_data['Redraw'] = True
        except AttributeError:
            pass
        self.screen_block_data = {}
        self.mid_point = [self.WIDTH // 2, self.HEIGHT // 2]
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE)
    
    def play(self):
    
        #Initialise screen
        pygame.init()
        self.setscreen()
        
        #Initialise game
        GT = GameTime(self.FPS, self.TICKS)
        self.state = 'Main'
        self.tilesize = TILESIZE
        self.noise_level = 15
        
        #Fill background
        self.screen.fill((255, 255, 255))
        
        #Camera
        self.cam = Camera(0, 0, 0.125)
        
        #Run inital code
        self.recalculate()
        self._world_draw()
        pygame.display.flip()
        while True:
            with GameTimeLoop(GT) as game_time:
                self.frame_data = {'Redraw': False,
                                   'Events': pygame.event.get(),
                                   'Keys': pygame.key.get_pressed(),
                                   'MousePos': pygame.mouse.get_pos(),
                                   'MouseClick': pygame.mouse.get_pressed()}
                if self.frame_data['Keys'][pygame.K_ESCAPE]:
                    pygame.quit()
                for event in self.frame_data['Events']:
                    if event.type == pygame.QUIT:
                        return
                    elif event.type == pygame.VIDEORESIZE:
                        self.WIDTH, self.HEIGHT = event.dict['size']
                        self.setscreen()
                        self.recalculate()
                #---MAIN LOOP START---
                
                if self.state == 'Main':
                    self.dk_core(game_time.ticks)
                
                
                
                #---MAIN LOOP END---
                if game_time.fps:
                    pygame.display.set_caption('{} {}'.format(game_time.fps, self.cam))
                    
                if self.frame_data['Redraw']:
                    self._world_draw()
                    pygame.display.flip()
                    self.screen.fill((255, 255, 255))
    
    def _world_draw(self):
        for coordinate in self.screen_coordinates:
            type, colour, location = self.screen_block_data[coordinate]
            pygame.draw.rect(self.screen, colour, (location[0], location[1], self.tilesize, self.tilesize))
    
    def get_tile_coords(self):
        click_segment = [split_num(i / self.tilesize) for i in self.frame_data['MousePos']]
        cam_data = ((self.cam.x_int, self.cam.x_float),
                    (self.cam.y_int, self.cam.y_float))
        tile = []
        for i, num in enumerate(cam_data):
            new_n_int = num[0] + click_segment[i][0]
            new_n_float = num[1] + click_segment[i][1]
            while new_n_float > 1:
                new_n_int += 1
                new_n_float -= 1
            tile.append(new_n_int)
        return tuple(tile)
        
    
    def dk_core(self, num_ticks):
        """Multiply values by num_ticks to keep a constant speed."""
        
        recalculate = False
        
        #Camera control
        if num_ticks:
            cam_up = -int(self.frame_data['Keys'][pygame.K_w])
            cam_down = int(self.frame_data['Keys'][pygame.K_s])
            cam_left = -int(self.frame_data['Keys'][pygame.K_a])
            cam_right = int(self.frame_data['Keys'][pygame.K_d])
            
            if cam_up or cam_down or cam_left or cam_right:
                self.cam.move(cam_left + cam_right, cam_up + cam_down, num_ticks)
                recalculate = True
            
        for event in self.frame_data['Events']:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.BLOCK_TAG.add(self.get_tile_coords())
                    recalculate = True
                    
            
        if recalculate:
            self.recalculate()
        
        
        if self.frame_data['Keys'][pygame.K_c]:
            print str(self.cam)
    
MainGame().play()
