import pygame
from pygame import mixer
import os
import random
import csv
from settings import *
mixer.init()
pygame.init()

# SCREEN_WIDTH and SCREEN_HEIGHT are now imported from settings.py
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

from entities import *
from world import *
from utils import *

###############	--- FRAMERATE --- ###############
# Game state variables
class Game:
	def __init__(self, screen):
		self.screen = screen
		self.clock = pygame.time.Clock()
		
		# Game variables
		self.level = 1
		self.start_game = False
		self.start_intro = False
		self.run = True
		
		# Player movement variables
		self.moving_left = False
		self.moving_right = False
		self.shoot = False
		self.grenade = False
		self.grenade_thrown = False
		
		# Fades
		self.intro_fade = ScreenFade(1, BROWN, 4)
		self.death_fade = ScreenFade(2, BROWN, 4)
		
		# Buttons
		self.start_button = Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 50, start_img, 0.2)
		self.exit_button = Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 80, exit_img, 0.2)
		self.restart_button = Button(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 50, restart_img, 0.2)
		
		self.load_level()

	def load_level(self):
		self.screen_scroll = 0
		self.bg_scroll = 0
		self.world_data = reset_level()
		# Load in level data and create world
		with open(f'level{self.level}_data.csv', newline='') as csvfile:
			reader = csv.reader(csvfile, delimiter=',')
			for x, row in enumerate(reader):
				for y, tile in enumerate(row):
					self.world_data[x][y] = int(tile)

		self.world = World()
		self.player, self.health_bar = self.world.process_data(self.world_data)

	def handle_events(self):
		for event in pygame.event.get():
			# quit game
			if event.type == pygame.QUIT:
				self.run = False
			# Keyboard presses
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_a or event.key == pygame.K_LEFT:
					self.moving_left = True
				if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
					self.moving_right = True
				if event.key == pygame.K_SPACE:
					self.shoot = True
				if event.key == pygame.K_q:
					self.grenade = True
				if (event.key == pygame.K_w or event.key == pygame.K_UP) and self.player.alive:
					self.player.jump = True
					jump_fx.play()
				if event.key == pygame.K_ESCAPE:
					self.run = False
			# Keyboard button releases
			if event.type == pygame.KEYUP:
				if event.key == pygame.K_a or event.key == pygame.K_LEFT:
					self.moving_left = False
				if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
					self.moving_right = False
				if event.key == pygame.K_SPACE:
					self.shoot = False
				if event.key == pygame.K_q:
					self.grenade = False
					self.grenade_thrown = False

	def update(self):
		# Update and draw groups
		bullet_group.update(self.player, enemy_group, self.world, self.screen_scroll)
		grenade_group.update(self.player, enemy_group, self.world, self.screen_scroll)
		decoration_group.update(self.screen_scroll)
		item_box_group.update(self.player, self.screen_scroll)
		exit_group.update(self.screen_scroll)
		explosion_group.update(self.screen_scroll)
		
		self.player.update()
		for enemy in enemy_group:
			enemy.ai(self.player, self.world, self.screen_scroll)
			enemy.update()

		if self.player.alive:
			# move the player
			self.screen_scroll, level_complete = self.player.move(self.moving_left, self.moving_right, self.world, self.bg_scroll)
			self.bg_scroll -= self.screen_scroll
			
			# CANDADO DE SEGURIDAD: Evita que el scroll sea negativo
			if self.bg_scroll < 0:
				self.player.hitbox.x += self.bg_scroll 
				self.bg_scroll = 0
			# CANDADO DE SEGURIDAD: Evita que el scroll pase del final del nivel
			max_scroll = (self.world.level_length * TILE_SIZE) - SCREEN_WIDTH
			if self.bg_scroll > max_scroll:
				self.player.hitbox.x += (self.bg_scroll - max_scroll)
				self.bg_scroll = max_scroll

			if self.shoot:
				self.player.update_action(4) # shoot 
				self.player.shoot() # Shoot
			elif self.grenade and not self.grenade_thrown and self.player.grenades > 0:
				grenade = Grenade(self.player.rect.centerx + (0.5 * self.player.rect.size[0] * self.player.direction), \
							self.player.rect.top, self.player.direction)
				grenade_group.add(grenade)
				self.player.grenades -= 1 # reduce the number of grenades
				self.grenade_thrown = True 
			elif self.player.in_air:
				self.player.update_action(2) # jump
			elif self.moving_left or self.moving_right:
				self.player.update_action(1) # running animation 
			else:
				self.player.update_action(0) # idle
				
			# check level completed
			if level_complete:
				self.start_intro = True
				self.bg_scroll = 0
				self.load_level()
		else:
			self.screen_scroll = 0

	def draw(self):
		if not self.start_game:
			self.screen.blit(welcome_img, (0, 0))
			if self.start_button.draw(self.screen):
				self.start_game = True
				self.start_intro = True
			if self.exit_button.draw(self.screen):
				self.run = False
		else:
			# draw background
			draw_bg(self.screen, self.bg_scroll) 
			
			# draw sprite groups
			decoration_group.draw(self.screen)
			item_box_group.draw(self.screen)
			bullet_group.draw(self.screen)
			grenade_group.draw(self.screen)
			exit_group.draw(self.screen)
			explosion_group.draw(self.screen)

			# Draw world map
			self.world.draw(self.screen, self.screen_scroll)
			
			# Show player health
			self.health_bar.draw(self.screen, self.player.health)
			
			# Show ammo
			draw_text(self.screen, f'Bullets: ', font, BROWN, 10, 10)
			for x in range(self.player.ammo):
				self.screen.blit(bullet_img, (100 + (x * 15), 15))
			
			# Show grenades
			draw_text(self.screen, f'Grenades: ', font, BROWN, 10, 40)
			for x in range(self.player.grenades):
				self.screen.blit(grenade_img, (120 + (x * 15), 40))
			
			self.player.draw(self.screen)
			for enemy in enemy_group:
				enemy.draw(self.screen)

			# Show intro
			if self.start_intro:
				if self.intro_fade.fade(self.screen):
					self.start_intro = False
					self.intro_fade.fade_counter = 0

			# Handle death
			if not self.player.alive:
				if self.death_fade.fade(self.screen):
					if self.restart_button.draw(self.screen):
						self.death_fade.fade_counter = 0
						self.start_intro = True
						self.load_level()

	def play(self):
		while self.run:
			self.clock.tick(FPS)
			self.handle_events()
			self.update()
			self.draw()
			pygame.display.update()
		pygame.quit()

# Initialize Game
if __name__ == '__main__':
	game = Game(screen)
	game.play()
