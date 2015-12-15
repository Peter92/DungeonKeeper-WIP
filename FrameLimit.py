from __future__ import division
import pygame
import time
import random

class GameTime(object):
    def __init__(self, desired_fps=120, desired_ticks=60):
        self.start_time = time.time()
        self.desired_fps = desired_fps
        self.desired_ticks = desired_ticks
        
        self.ticks = 0
        
        self.framerate_counter = 1
        self.framerate_time = 0
        
    def calculate_ticks(self, current_time):
        """Ensure the correct number of ticks have passed since the 
        start of the game.
        This doesn't use the inbuilt pygame ticks.
        """
        time_elapsed = current_time - self.start_time
        
        total_ticks_needed = int(time_elapsed * self.desired_ticks)
        
        ticks_this_frame = total_ticks_needed - self.ticks
        self.ticks += ticks_this_frame
        
        return ticks_this_frame
    
    def calculate_fps(self, current_time, update_time=0.1):
        """Calculate the FPS from actual time, not ticks.
        
        It will return a number every update_time seconds, and will
        return None any other time.
        """
        frame_time = current_time - self.framerate_time
        
        if frame_time < update_time:
            self.framerate_counter += 1
            
        else:
            self.framerate_time = current_time
            fps = self.framerate_counter / frame_time
            self.framerate_counter = 1
            return int(fps)
        
    def limit_fps(self, alternate_fps=None):
        
        wanted_fps = alternate_fps or self.desired_fps
        if wanted_fps:
            pygame.time.Clock().tick(wanted_fps)

class GameTimeLoop(object):
    """This gets called every loop but uses GameTime."""
    
    def __init__(self, GTObject):
    
        self.GTObject = GTObject
        GTObject.loop_start = time.time()
        
        #Run the code once so the result can be called multiple times
        self.ticks = GTObject.calculate_ticks(GTObject.loop_start)
        self.fps = GTObject.calculate_fps(GTObject.loop_start)
        
        self.temp_fps = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.GTObject.limit_fps(self.temp_fps)
        self.temp_fps = None
        
    def set_fps(self, fps):
        self.GTObject.desired_fps = fps
    
    def temp_fps(self, fps):
        self.temp_fps = fps
    
    def update_ticks(self, ticks):
        self.GTObject.start_time = time.time()
        self.GTObject.desired_ticks = ticks
        self.ticks = 0
        
#Example use
def game():
    
    pygame.init()
    screen = pygame.display.set_mode((640, 480))

    #clock = pygame.time.Clock()
    max_fps = None
    ticks_per_second = 60
    FrameRate = GameTime(max_fps, ticks_per_second)

    move_speed = 0.175
    move_total = 0
    
    while True:
        with GameTimeLoop(FrameRate) as frame_time:
        
            fps = frame_time.fps
            if fps:
                pygame.display.set_caption(str(fps))
            
            #Calculations to be done once per tick
            #Can multiply by the number of ticks or do a loop
            ticks_this_frame = frame_time.ticks
            for tick in xrange(frame_time.ticks):
                pass
            
            
            #Do normal stuff here
            move_total += move_speed * ticks_this_frame
            print move_total  #Just print this to show it's correctly staying at the same speed
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                #Set a new fps
                if event.type == pygame.MOUSEBUTTONDOWN:
                    new_fps = random.choice((None, 1, 5, 10, 30, 60, 120, 1000, 10000))
                    print 'set fps to: {}'.format(new_fps)
                    frame_time.set_fps(new_fps)

if __name__ == '__main__':
    game()
