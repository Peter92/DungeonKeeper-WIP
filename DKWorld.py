import pygame

BLACK = (0,   0,   0  )
BROWN = (153, 76,  0  )
GREEN = (0,   255, 0  )
BLUE  = (0,   0,   255)
WHITE = (255, 255, 255)


DIRT = 0
GRASS = 1
WATER = 2
COAL = 3


TILECOLOURS = {
    DIRT  : BROWN,
    GRASS : GREEN,
    WATER : BLUE,
    COAL  : BLACK
}

#Test case
TILEMAP = {
    (-1, -2): GRASS,
    ( 0, -2): COAL,
    ( 1, -2): DIRT,
    (-1, -1): WATER,
    ( 0, -1): WATER,
    ( 1, -1): GRASS,
    (-1,  0): COAL,
    ( 0,  0): GRASS,
    ( 1,  0): WATER,
    (-1,  1): DIRT,
    ( 0,  1): GRASS,
    ( 1,  1): COAL,
    (-1,  2): GRASS,
    ( 0,  2): WATER,
    ( 1,  2): DIRT
}

#Build a circle
for x in range(-50, 50):
    for y in range(-50, 50):
        if x ** 2 + y ** 2 < 500:
            TILEMAP[(x, y)] = GRASS

TILESIZE = 40
DEFAULTTILE = WATER

def get_tile(x, y=None):
    """Function that can be updated to something better in the future."""
    if y is None:
        x, y = x
    try:
        return TILEMAP[(x, y)]
    except KeyError:
        return DEFAULTTILE
