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
		self.pause = False
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
		
		# Buttons (Main/Pause Menu - Fixed Coordinates)
		self.start_button = Button(SCREEN_WIDTH // 2 - 135, SCREEN_HEIGHT // 2 - 60, start_img, 0.14)
		self.load_button = Button(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 35, load_img, 0.14)
		self.exit_button = Button(SCREEN_WIDTH // 2 - 85, SCREEN_HEIGHT // 2 + 130, exit_img, 0.13)
		# Place Resume at Load's position: X-140, Y+35
		self.resume_button = Button(SCREEN_WIDTH // 2 - 125, SCREEN_HEIGHT // 2 + 15, resume_img, 0.14)
		
		# In-game/Special Buttons
		self.restart_button = Button(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 50, restart_img, 0.14)
		self.restart_small_button = Button(SCREEN_WIDTH - 42, 50, restart_small_img, 1)
		self.save_button = Button(SCREEN_WIDTH - 39, 100, save_small_img, 1)
		self.menu_button = Button(SCREEN_WIDTH - 40, 150, menu_small_img, 1)
		self.pause_button = Button(SCREEN_WIDTH - 40, 200, pause_img, 1)
		
		# Confirmation Buttons (Moved down to avoid overlap with menu buttons)
		self.yes_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, yes_img, 0.1)
		self.no_button = Button(SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT // 2, no_img, 0.1)
		
		self.confirming_action = None # Possible values: 'save', 'restart', 'menu', None
		self.action_cooldown = 0 # Safety timer to avoid accidental double clicks
		
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

	def save_game(self, filename='saved_game.json'):
		# Collect remaining items and their absolute world positions
		items_list = []
		for item in item_box_group:
			items_list.append({
				'item_type': item.item_type,
				'x': item.rect.x + self.bg_scroll, # Absolute World X
				'y': item.rect.y
			})
		
		# Collect alive enemies and their states
		enemies_list = []
		for enemy in enemy_group:
			if enemy.alive:
				enemies_list.append({
					'x': enemy.hitbox.x + self.bg_scroll, # Absolute World X
					'y': enemy.hitbox.y,
					'health': enemy.health,
					'direction': enemy.direction,
					'move_counter': enemy.move_counter
				})
		
		save_data = {
			'level': self.level,
			'health': self.player.health,
			'ammo': self.player.ammo,
			'grenades': self.player.grenades,
			'player_x': self.player.hitbox.x + self.bg_scroll, # Absolute World X
			'player_y': self.player.hitbox.y,
			'bg_scroll': self.bg_scroll,
			'items': items_list,
			'enemies': enemies_list
		}
		save_game_json(save_data, filename)
		print(f"Game Saved to {filename}!")

	def save_current_game(self):
		self.save_game('current_game.json')

	def load_game(self, filename='saved_game.json'):
		data = load_game_json(filename)
		if data:
			self.level = data['level']
			self.load_level() # This resets groups and loads world data
			
			# Restore camera scroll
			self.bg_scroll = data['bg_scroll']
			
			# Shift all level-loaded sprites and tiles by the restored scroll
			for tile in self.world.obstacle_list:
				tile[1].x -= self.bg_scroll
			for decoration in decoration_group:
				decoration.rect.x -= self.bg_scroll
			for exit_obj in exit_group:
				exit_obj.rect.x -= self.bg_scroll

			# Restore player state
			self.player.health = data['health']
			self.player.ammo = data['ammo']
			self.player.grenades = data['grenades']
			
			# Restore player position (Absolute World X -> Screen position)
			self.player.hitbox.x = data['player_x'] - self.bg_scroll
			self.player.hitbox.y = data['player_y']
			self.player.rect.center = self.player.hitbox.center
			
			# Restore items: clear those created by load_level and use saved ones
			item_box_group.empty()
			for item_data in data['items']:
				# We use dummy (0,0) and then correct rect.x/y to avoid re-calculating midtop math
				item_box = ItemBox(item_data['item_type'], 0, 0)
				item_box.rect.x = item_data['x'] - self.bg_scroll
				item_box.rect.y = item_data['y']
				item_box_group.add(item_box)
			
			# Restore enemies: clear those created by load_level and use saved ones
			enemy_group.empty()
			for enemy_data in data['enemies']:
				# Note: enemies use scale 0.11 and speed 2 as per world.py
				enemy = Enemy(0, 0, 0.11, 2, 20, 0)
				enemy.health = enemy_data['health']
				enemy.direction = enemy_data['direction']
				enemy.move_counter = enemy_data.get('move_counter', 0)
				enemy.flip = True if enemy.direction == -1 else False
				enemy.hitbox.x = enemy_data['x'] - self.bg_scroll
				enemy.hitbox.y = enemy_data['y']
				enemy.rect.center = enemy.hitbox.center
				enemy_group.add(enemy)
			
			print(f"Game Loaded from {filename}!")
		else:
			print(f"No save game found for {filename}.")

	def load_current_game(self):
		self.load_game('current_game.json')

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
					if self.start_game:
						self.pause = not self.pause
					else:
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
			# Safety check: don't allow menu clicks if we just came from a confirmation
			if self.action_cooldown > 0:
				self.action_cooldown -= 1
				return

			if self.pause:
				# --- PAUSE MENU ---
				# Top: New Game (Start Button)
				if self.start_button.draw(self.screen):
					self.level = 1
					self.load_level()
					self.start_game = True
					self.pause = False
					self.start_intro = True
				
				# Middle: Resume (Where Load was)
				if self.resume_button.draw(self.screen):
					self.start_game = True
					self.load_current_game()
					self.pause = False
					self.start_intro = True
					
				# Bottom: Exit
				if self.exit_button.draw(self.screen):
					self.run = False
			else:
				# --- MAIN MENU ---
				# Top: Start
				if self.start_button.draw(self.screen):
					self.start_game = True
					self.start_intro = True

				# Middle: Load
				if self.load_button.draw(self.screen):
					self.start_game = True
					self.load_game() # Permanent save
					self.start_intro = True
				
				# Bottom: Exit
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
			draw_text(self.screen, f'Bullets: ', font_small, BROWN, 10, 10)
			for x in range(self.player.ammo):
				self.screen.blit(bullet_img, (100 + (x * 15), 15))
			
			# Show grenades
			draw_text(self.screen, f'Grenades: ', font_small, BROWN, 10, 40)
			for x in range(self.player.grenades):
				self.screen.blit(grenade_img, (120 + (x * 15), 40))
			
			# Draw in-game control buttons (only if player is alive and not confirming/paused)
			if self.player.alive and not self.confirming_action and not self.pause:
				if self.restart_small_button.draw(self.screen):
					self.confirming_action = 'restart'
				if self.save_button.draw(self.screen):
					self.confirming_action = 'save'
				if self.menu_button.draw(self.screen):
					self.confirming_action = 'menu'
				if self.pause_button.draw(self.screen):
					self.pause = True
			
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
					draw_text(self.screen, "Game Over!", font_big, WHITE, SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT // 2 - 200)
					if self.start_button.draw(self.screen):
						self.death_fade.fade_counter = 0
						self.start_intro = True
						self.load_level()
					if self.exit_button.draw(self.screen):
						self.start_game = False
			
			# --- CONFIRMATION OVERLAY ---
			if self.confirming_action:
				# Darken background
				overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
				overlay.set_alpha(100)
				overlay.fill((0, 0, 0))
				self.screen.blit(overlay, (0, 0))
				
				# Show message
				msg = ""
				if self.confirming_action == 'save':
					msg = "   ¿Are you sure you want to save game?"
				elif self.confirming_action == 'restart':
					msg = "¿Restart Game? (You will lose game progress)"
				elif self.confirming_action == 'menu':
					msg = "¿Go to Menu? (You will lose game progress)"
				
				draw_text(self.screen, msg, font_medium, WHITE, SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2 - 50)
				
				# Yes / No buttons
				if self.yes_button.draw(self.screen):
					if self.confirming_action == 'save':
						self.save_game()
						self.confirming_action = None
					elif self.confirming_action == 'restart':
						self.death_fade.fade_counter = 0
						self.start_intro = True
						self.load_level()
						self.confirming_action = None
					elif self.confirming_action == 'menu':
						self.start_game = False
						self.pause = False 
						self.confirming_action = None
						self.action_cooldown = 15 # Wait 15 frames before allowing menu clicks
						
				if self.no_button.draw(self.screen):
					self.confirming_action = None

			# --- PAUSE OVERLAY ---
			if self.pause:
				# Darken background
				overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
				overlay.set_alpha(150)
				overlay.fill((0, 0, 0))
				self.screen.blit(overlay, (0, 0))
				
				draw_text(self.screen, "GAME PAUSED", font_medium, WHITE, SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 - 50)
				
				# Resume button at slot 2 position
				if self.resume_button.draw(self.screen):
					self.pause = False
				
				# Exit button at slot 3 position
				if self.exit_button.draw(self.screen):
					self.start_game = False
					self.pause = False

	def play(self):
		while self.run:
			self.clock.tick(FPS)
			self.handle_events()
			# Only update game if active, not paused, and not confirming
			if self.start_game and not self.pause and not self.confirming_action:
				self.update()
			self.draw()
			pygame.display.update()
		pygame.quit()

# Initialize Game
if __name__ == '__main__':
	game = Game(screen)
	game.play()
