import pygame
import os
import random
from settings import *

# Initialize mixer for sounds
pygame.mixer.init()

############### --- MUSIC & SOUNDS --- ###############
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 500)

jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)

############### --- IMAGES --- ###############
# Button
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
load_img = pygame.image.load('img/load_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()

# Background images
mountain_img = pygame.image.load('img/Background/BG.png').convert_alpha()
welcome_img = pygame.image.load('img/Background/welcome.png').convert_alpha()
welcome_img = pygame.transform.scale(welcome_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Entity images
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()

item_boxes = {
	'Health' : health_box_img,
	'Ammo' : ammo_box_img,
	'Grenade' : grenade_box_img
}

# Global Cache for Assets
animation_cache = {}
tile_cache = []
explosion_cache = []

def load_character_animations(char_type, scale):
	# Check if animations are already in cache
	if char_type in animation_cache:
		return animation_cache[char_type]
	
	# If not in cache, load them from disk
	animation_list = []
	animation_types = ['Idle', 'Run', 'Jump', 'Death', 'Shoot']
	for animation in animation_types:
		temp_list = []
		path = f'img/{char_type}/{animation}'
		if os.path.exists(path):
			files = [f for f in os.listdir(path) if f.endswith('.png')]
			num_of_frames = len(files)
			for i in range(num_of_frames):
				img = pygame.image.load(f'{path}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
		animation_list.append(temp_list)
	
	animation_cache[char_type] = animation_list
	return animation_list

def load_tiles():
	global tile_cache
	if tile_cache: return tile_cache
	
	for x in range(TILE_TYPES):
		img = pygame.image.load(f'img/Tile/{x}.png')
		w = TILE_SIZE
		h = TILE_SIZE
		decoration_scales = {
			16: 1.0, 17: 1.0, 18: 0.7, 19: 0.5, 20: 0.7,
			21: 0.8, 22: 0.8, 23: 0.6, 24: 0.6, 25: 0.5
		}
		if x in decoration_scales:
			scale = decoration_scales[x]
			w = int(img.get_width() * scale)
			h = int(img.get_height() * scale)
		img = pygame.transform.scale(img, (w, h))
		tile_cache.append(img)
	return tile_cache

def load_explosion_animations(scale):
	global explosion_cache
	if explosion_cache: return explosion_cache
	
	for num in range(1, 6):
		img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
		img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
		explosion_cache.append(img)
	return explosion_cache

# Store tiles in a list (Lazy load or pre-load once)
img_list = load_tiles()

############### --- SPRITE GROUPS --- ###############
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#### BASE CHARACTER CLASS ###
class BaseCharacter(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = min(ammo, MAX_AMMO)
		self.start_ammo = self.ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = load_character_animations(self.char_type, scale)
		self.frame_index = 0
		self.action = 0 # 0:Idle, 1:Run, 2:Jump, 3:Death, 4:Shoot
		self.update_time = pygame.time.get_ticks()
		
		# Rectangle and Hitbox
		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.5, self.rect.height * 0.9)
		self.hitbox.center = self.rect.center

	def update(self):
		self.update_animation()
		self.check_alive()
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1

	def move(self, dx, dy, world):
		# Standard physics collision for all characters
		# Collisions
		for tile in world.obstacle_list:
			# check collision in the x direction
			if tile[1].colliderect(self.hitbox.x + dx, self.hitbox.y, self.hitbox.width, self.hitbox.height):
				dx = 0
			# check for collisions in the 'y' direction
			if tile[1].colliderect(self.hitbox.x, self.hitbox.y + dy, self.hitbox.width, self.hitbox.height):
				if self.vel_y < 0: # jumping
					self.vel_y = 0
					dy = tile[1].bottom - self.hitbox.top
				elif self.vel_y >= 0: # falling
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.hitbox.bottom
		
		# Update positions
		self.hitbox.x += dx
		self.hitbox.y += dy
		self.rect.center = self.hitbox.center
		
		return dx, dy

	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo -= 1
			shot_fx.play()

	def update_animation(self):
		ANIMATION_COOLDOWN = 100
		self.image = self.animation_list[self.action][self.frame_index]
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3: # Death
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0

	def update_action(self, new_action):
		if new_action != self.action:
			self.action = new_action
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()

	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)

	def draw(self, screen):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


#### PLAYER CLASS ###
class Player(BaseCharacter):
	def __init__(self, x, y, scale, speed, ammo, grenades):
		super().__init__('player', x, y, scale, speed, ammo, grenades)

	def move(self, moving_left, moving_right, world, bg_scroll):
		screen_scroll = 0
		dx = 0
		dy = 0
		
		# Movement logic
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1
		
		if self.jump and not self.in_air:
			self.vel_y = -11
			self.jump = False
			self.in_air = True
			
		self.vel_y += GRAVITY
		if self.vel_y > 10: self.vel_y = 10
		dy += self.vel_y

		# Tile collisions from base
		dx, dy = super().move(dx, dy, world)

		# Player-specific: Exit and Fall death
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0

		# Prevent going off screen (clamping)
		if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
			# If we hit the absolute screen edges and there's no more scroll
			pass # Actual logic handled by scroll blocks below

		# Scroll logic
		if self.hitbox.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH:
			self.hitbox.x -= dx
			screen_scroll = -dx
		elif self.hitbox.left < SCROLL_THRESH and bg_scroll > 0:
			self.hitbox.x -= dx
			screen_scroll = -dx
		
		self.rect.center = self.hitbox.center
		return screen_scroll, level_complete


#### ENEMY CLASS ###
class Enemy(BaseCharacter):
	def __init__(self, x, y, scale, speed, ammo, grenades):
		super().__init__('enemy', x, y, scale, speed, ammo, grenades)
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idiling_counter = 0

	def ai(self, player, world, screen_scroll):
		if self.alive and player.alive:
			if not self.idling and random.randint(1, 200) == 1:
				self.update_action(0)
				self.idling = True
				self.idiling_counter = 50
			
			self.vision.center = (self.hitbox.centerx + 75 * self.direction, self.hitbox.centery)
			
			if self.vision.colliderect(player.hitbox):
				self.update_action(0)
				self.shoot()
			else:
				if not self.idling:
					# Simple AI movement
					dx = self.direction * self.speed
					self.flip = self.direction == -1
					
					# Basic gravity for enemy
					self.vel_y += GRAVITY
					if self.vel_y > 10: self.vel_y = 10
					dy = self.vel_y
					
					# Use base character movement
					super().move(dx, dy, world)
					self.update_action(1)
					
					self.move_counter += 1
					if self.move_counter > TILE_SIZE * 3:
						self.direction *= -1
						self.move_counter = -1
				else:
					self.idiling_counter -= 1
					if self.idiling_counter <= 0:
						self.idling = False
		
		# Apply screen scroll to enemy
		self.hitbox.x += screen_scroll
		self.rect.center = self.hitbox.center

### DECORATION CLASS ###
class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img # Pull already scaled image from world loading
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self, screen_scroll):
		self.rect.x += screen_scroll

### EXIT CLASS ###
class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
	def update(self, screen_scroll):
		self.rect.x += screen_scroll

### ITEMSBOX CLASS ###
class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type] # Access the dictionary to get the item
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self, player, screen_scroll):
		# scroll
		self.rect.x += screen_scroll
		# Check if the player has picked up the box
		if player and hasattr(player, 'rect'):
			if self.rect.colliderect(player.rect):
				# Check what kind of box it was
				if self.item_type == 'Health':
					player.health += 25
					if player.health > player.max_health:
						player.health = player.max_health
				elif self.item_type == 'Ammo':
					player.ammo += 5
					if player.ammo > MAX_AMMO:
						player.ammo = MAX_AMMO
				elif self.item_type == 'Grenade':
					player.grenades += 3
				# Delete the item
				self.kill()

### HEALTHBAR CLASS ###
class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = health

	def draw(self, screen, health):
		# Update with new health
		self.health = health
		# Calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

### BULLET CLASS ###
class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction
	
	def update(self, player, enemy_group, world, screen_scroll):
		# Move the bullet
		self.rect.x += (self.direction * self.speed) + screen_scroll
		# Check if the bullet left the screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill() # clean memory
		# check for collisions with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()
		# Collisions with other objects
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()

### GRENADE CLASS ###
class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 5
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction
	
	def update(self, player, enemy_group, world, screen_scroll):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y
		#check for collision with level
		for tile in world.obstacle_list:
			# Check if the grenade hits a walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y + dy, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed
			# check for collisions in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				# check if bellow the ground, i.e. thrown up
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				# check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom
		# Update grenade's position
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		# Countdown for the explosion
		self.timer -= 1
		if self.timer <= 0:
			grenade_fx.play()
			self.kill()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			# Do damage to anyone that is nearby
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 50
			
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health -= 50

### FADE CLASS ###
class ScreenFade():
	def __init__(self, direction, colour, speed):
		self.direction = direction
		self.colour = colour
		self.speed = speed
		self.fade_counter = 0

	def fade(self, screen):
		fade_complete = False
		self.fade_counter += self.speed

		if self.direction == 1: # whole screen fade
			pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH , SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
			pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH , SCREEN_HEIGHT))

		if self.direction == 2: # vertical fade
			pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
		
		if self.fade_counter >= SCREEN_WIDTH:
			fade_complete = True

		return fade_complete

### EXPLOSION CLASS ###
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = load_explosion_animations(scale)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0
	
	def update(self, screen_scroll):
		# scroll
		self.rect.x += screen_scroll
		EXPLOSION_SPEED = 4
		# Update explosion animation
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			# If the animation is complete, delete the explosion
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]
