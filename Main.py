from __future__ import division
import time
import pygame
import math
from RPGCore import Movement, split_decimal_part
from decimal import getcontext, Decimal as d
_default_precision = getcontext().prec

class Player(object):
    """Class to store the player data."""

    def __init__(self, start=(0, 0, 0), bearing=0,
                 speed_max=1, speed_accel=3, speed_damp=4, 
                 turn_max=4, turn_accel=16, turn_damp=100000):
        
        self.loc = Movement(start, block_size=256)
        self.bearing = 0
        
        self.speed_max = speed_max
        self.speed_accel = speed_accel
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
        return [d(i) * d(speed) for i in (self.rx, self.ry, self.rz)]
    
    def step(self, frame_time):
    
        frame_time = d(frame_time)
        
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
            self.loc = Movement(*update, block_size=256)
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
        len_int = len(str(speed_increment[1]))
        if len_int > current_precision:
            getcontext().prec = len_int
        elif current_precision != _default_precision and len_int < _default_precision:
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
    
    def _game_core(self):
    
        move_forward = self._keys[pygame.K_w]
        move_backward = self._keys[pygame.K_s]
        turn_left = self._keys[pygame.K_a]
        turn_right = self._keys[pygame.K_d]
        if move_forward:
            self.player.move(frame_time=self._frame_time)
        if move_backward:
            self.player.move(frame_time=self._frame_time, backwards=True)
        if turn_left:
            self.player.turn(frame_time=self._frame_time)
        if turn_right:
            self.player.turn(frame_time=self._frame_time, backwards=True)
        
        #print self.player.coordinates(), self.player.speed, self.player.bearing, self.player.turning
        '''
        n = 1000
        if not self.num_frames % n:
            self.cur_time = time.time()
            try:
                print n/(self.cur_time-self.old_time)
            except AttributeError:
                pass
            except ZeroDivisionError:
                pass
            #print int(self.player.speed[1]), self.player.coordinates()[1], self.player.loc.raw[1]
            print self.player.loc.raw[1]
            print split_decimal_part(self.player.speed[1])
            self.player.speed_accel *= 2
            self.old_time = self.cur_time
            '''
            
            
        self.player.step(self._frame_time)
        
        
    def play(self):
        pygame.init()
        
        #Initialise screen
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption('Basic RPG')
        self.clock = pygame.time.Clock()

        #Fill background
        self.screen.fill((255, 255, 255))
        
        #Initialise player and movement
        speed_mult = 100
        self.player = Player(speed_max=1 * speed_mult, 
                             speed_accel=3 * speed_mult,  
                             speed_damp=4 * speed_mult, 
                             bearing=0)
        
        #Initialise camera
        self.camera = [0, 0]
        
        time_current = time_last = time.time()
        self.num_frames = 0
        
        while True:
            self.num_frames += 1
            time_current = time.time()
            #self.clock.tick(60)
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
                    pass
            
            self._game_core()
            print self.player.loc.raw
            
            #c = [int(round(float(i))) for i in self.player.coordinates()]
            #self.screen.set_at((c[0], c[1]), (0, 0, 0))
            if self._redraw:
                pygame.display.flip()
            time_last = time_current
            
MainGame().play()
