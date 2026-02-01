import pygame
import json
import os
from settings import *
from entities import *

pygame.font.init()
font_small = pygame.font.SysFont('Futura', 25)
font_medium = pygame.font.SysFont('Futura', 40)
font_big = pygame.font.SysFont('Futura', 90)

### BUTTON CLASS ###
class Button():
	def __init__(self, x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False
	
	def draw(self, surface):
		action = False

		# get mouse position
		pos = pygame.mouse.get_pos()

		# check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1  and self.clicked == False:
				action = True
				self.clicked = True
		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False
		# draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action

### Draw text
def draw_text(screen, text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

### Draw Background
def draw_bg(screen, bg_scroll):
	screen.fill(BG)
	width = mountain_img.get_width()
	for x in range(5):
		screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height()))

### Restart level
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	exit_group.empty()

	# create empty tile list
	data = []
	for row in range(ROWS):
		r = [-1] * COLS # List of 150 entries of -1
		data.append(r)
	return data

### Save data to JSON
def save_game_json(data, filename='saved_game.json'):
	with open(filename, 'w') as f:
		json.dump(data, f, indent=4)

### Load data from JSON
def load_game_json(filename='saved_game.json'):
	if os.path.exists(filename):
		with open(filename, 'r') as f:
			return json.load(f)
	return None
