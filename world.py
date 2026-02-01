import pygame
import csv
from settings import *
from entities import *

### WORLD CLASS ###
class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0]) #How many tiles there are in one row
		# iterate through each value in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile] # pull the image from the list
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect) # tupla

					if tile >= 0 and tile <= 15:
						self.obstacle_list.append(tile_data)
					elif tile >= 16  and tile <= 25:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE) 
						decoration_group.add(decoration)
					elif tile == 26: # create health box
						item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 27: # create ammo box
						item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 28: # Create grenade box
						item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 29:
						exit = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit )
					elif tile == 31: # create player
						player = Player(x * TILE_SIZE, y * TILE_SIZE, 0.1, 5, 20 , 5)
						health_bar = HealthBar(SCREEN_WIDTH - 160, 10, player.health, player.health)
					elif tile == 30: # create enemy
						enemy = Enemy(x * TILE_SIZE, y * TILE_SIZE, 0.11, 2, 20, 0)
						enemy_group.add(enemy)
				
		return player, health_bar
	
	def draw(self, screen, screen_scroll):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])
