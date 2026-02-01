import pygame

############### --- SCREEN --- ###############
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

############### --- FRAMERATE --- ###############
FPS = 60

############### --- GAME VARIABLES --- ###############
GRAVITY = 0.65
SCROLL_THRESH = 200 # Distance the player can get to the edge of the screen before it starts to scroll
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 32
MAX_LEVEL = 3
MAX_AMMO = 30

############### --- COLORS --- ###############
BG = (25, 39, 43)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)
BROWN = (47, 30, 30)
