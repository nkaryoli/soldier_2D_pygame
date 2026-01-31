import pygame
from pygame import mixer
import os
import random
import csv

mixer.init()
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

###############	--- FRAMERATE --- ###############
clock =  pygame.time.Clock()
FPS = 60

############### --- GAME VARIABLES --- ###############
GRAVITY = 0.65
SCROLL_THRESH = 200 # Distance the player can get to the edge of the screen before it starts to scroll
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 32
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
MAX_LEVEL = 3

############### --- ACTION VARIABLES --- ###############
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

############### --- MUSIC ---	###############
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 500)

jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)

shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)

grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)

############### --- IMAGES ---	###############
# Button
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()

# Background images
# pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
# pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/BG.png').convert_alpha()
# sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()

# Bullets
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()

# Grenades
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()

# Pic up booxes
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
	'Health' : health_box_img,
	'Ammo' : ammo_box_img,
	'Grenade' : grenade_box_img
}

# Store tiles in a list
img_list = []

for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/Tile/{x}.png')
	w = TILE_SIZE
	h = TILE_SIZE

	# Definir escalas personalizadas para tiles de decoración
	decoration_scales = {
		16: 1.0,
		17: 1.0,
		18: 0.7,
		19: 0.5,
		20: 0.7,
		21: 0.8,
		22: 0.8,
		23: 0.6,
		24: 0.6,
		25: 0.5
	}

	# Aplicar escala si el tile está en el diccionario
	if x in decoration_scales:
		scale = decoration_scales[x]
		w = int(img.get_width() * scale)
		h = int(img.get_height() * scale)

	img = pygame.transform.scale(img, (w, h))
	img_list.append(img)

################ --- COLORS --- ###############
BG = (25,39,43)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

############### --- HELPER FUNCTIONS --- ###############idle

# Define Fontç
font = pygame.font.SysFont('Futura', 30)

### Draw text
def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

### Draw Background
def draw_bg():
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

############### --- CLASSES --- ###############

#### SOLDIER CLASS ###
class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades): # CONSTRUCTOR
		pygame.sprite.Sprite.__init__(self) # to inherit pygame's functionalities
		self.alive = True
		self.char_type = char_type
		self.speed = speed # assign the parameter to the instance
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0 # index that indicates which animation I'm in
		self.update_time = pygame.time.get_ticks()
		# AI specific variable
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idiling_counter = 0

		# Load all animations for the player
		animation_types = ['Idle', 'Run', 'Jump' , 'Death', 'Shoot']
		for animation in animation_types:
			temp_list = [] # temporary list to store animation groups
			# Count files in the folder
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha() 
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale))) # Scale the image since it's too big
				temp_list.append(img)
			self.animation_list.append(temp_list) # save temp_list in the animations list

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect() # rectangle around the image
		self.rect.center = (x, y) # place the rect in the position received as parameter
		self.width = self.image.get_width()
		self.height = self.image.get_height()

		self.hitbox = pygame.Rect(0, 0, self.rect.width * 0.5, self.rect.height * 0.9) # rect aroun player for collisions
		self.hitbox.center = self.rect.center

	def update(self):
		self.update_animation()
		self.check_alive()
		# Update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1

	def move(self, moving_left, moving_right):
		global bg_scroll
		# Reset movement variables
		screen_scroll = 0
		dx = 0
		dy = 0
		
		# Assign movement to variables depending on how player is moving
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1
		# Jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True
		# Gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y

		# COLLISIONS
		for tile in world.obstacle_list:
			#check collision in the x direction
			if tile[1].colliderect(self.hitbox.x + dx, self.hitbox.y, self.hitbox.width, self.hitbox.height):
				dx = 0

			# check for collisions in the 'y' direction
			if tile[1].colliderect(self.hitbox.x, self.hitbox.y + dy, self.hitbox.width, self.hitbox.height):
				# check if bellow the ground, i.e. jumping
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.hitbox.top
				# check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.hitbox.bottom

		# collision with exit
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		# if palyer falls
		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0

		# check if goinf off the edges of the screen
		if self.char_type == 'player':
			if self.rect.left + dx < 0 or self.rect.right +dx > SCREEN_WIDTH:
				dx = 0

		# update scroll based on player position
		if self.char_type == 'player':
			# Scroll hacia la derecha
			if self.hitbox.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH:
				self.hitbox.x -= dx
				screen_scroll = -dx
			# Scroll hacia la izquierda
			elif self.hitbox.left < SCROLL_THRESH and bg_scroll > 0:
				self.hitbox.x -= dx
				screen_scroll = -dx

		# move hitbox (FÍSICA)
		self.hitbox.x += dx
		self.hitbox.y += dy

		# synchronize sprite with hitbox (VISUALLY)
		self.rect.center = self.hitbox.center
	
		return screen_scroll, level_complete

	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo -= 1
			shot_fx.play()

		
	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0) # idle animation
				self.idling = True
				self.idiling_counter = 50
			
			# Update ai vision as the enemy moves
			self.vision.center = (self.hitbox.centerx + 75 * self.direction, self.hitbox.centery)
			# pygame.draw.rect(screen, RED, self.vision, 1) #área de visión
			
			# Check if the ai is near the player
			if self.vision.colliderect(player.hitbox):
				# Stop running and face player
				self.update_action(0) # idle 
				# Shoot the player
				self.shoot()
			# If it does not 'see' the player, continue with patrol
			else:
				# Patrolling
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False

					ai_moving_left = not ai_moving_right
					# Move ai
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1) # run animation
					self.move_counter += 1

					if self.move_counter > TILE_SIZE * 3:
						self.direction *= -1
						self.move_counter = -1
				else:
					self.idiling_counter -= 1
					if self.idiling_counter <= 0:
						self.idling = False
		# scroll
		self.hitbox.x += screen_scroll
		self.rect.center = self.hitbox.center


	def update_animation(self):
		# Update animation
		ANIMATION_COOLDOWN = 100
		# Update image depending on the frame and current animation
		self.image = self.animation_list[self.action][self.frame_index]
		# Check if enough time has passed since the last update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks() # update the instance time
			self.frame_index += 1 # move to the next index in the list
		# If the animation has reached the last index in the list
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1 # if it's DEATH, stop the animation
			else:
				self.frame_index = 0 # For the rest, reset it to the beginning

	def update_action(self, new_action):
		# Check if the current animation is different from the previous one
		if new_action != self.action:
			self.action = new_action
			# Update the animation configuration
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()

	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3) # play death animation

	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

###

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
					img = img_list[tile] # pull the image form the list
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
						player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 0.1, 5, 20 , 5) # instance(player) from the Soldier class
						health_bar = HealthBar(10, 10, player.health, player.health) # instance of the HealthBar class
					elif tile == 30: # create enemy
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 0.11, 2, 20, 0) # instance(enemy) from the Soldier class
						enemy_group.add(enemy)
				
		return player, health_bar
	
	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])
###

### DECORATION CLASS ###
class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)

		# scale image
		w = img.get_width()
		h = img.get_height()

		self.image = pygame.transform.scale(img, (w, h)).convert_alpha()
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll
###

### EXIT CLASS ###
class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
	def update(self):
		self.rect.x += screen_scroll
##

### ITEMSBOX CLASS ###
class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type] # Accesd the dictionary to get the item
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		# scroll
		self.rect.x += screen_scroll
		# Check if the player has picked up the box
		if pygame.sprite.collide_rect(self, player):
			# Check what king of box it was
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo += 15
			elif self.item_type == 'Grenade':
				player.grenades += 3
			# Delete the item
			self.kill()
###

### HEALTHBAR CLASS ###
class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = health

	def draw(self, health):
		# Update with new health
		self.health = health
		# Calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))
###

### BULLET CLASS ###
class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction
	
	def update(self):
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
###

### GRENADE CLASS ###
class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction
	
	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y
		#check for collision with level
		for tile in world.obstacle_list:
			# Check if the grenade hits a walls
			if tile[1].colliderect(self.rect.x +dx, self.rect.y + dy, self.width, self.height):
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
###

### EXPLOSION CLASS ###
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png')
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0
	
	def update(self):
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
##

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
###

############### --- CREATE BUTTONS --- ###############
start_button = Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 140, start_img, 0.9)
exit_button = Button(SCREEN_WIDTH // 2 - 105, SCREEN_HEIGHT // 2 + 30, exit_img, 0.8)
restart_button = Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

############### --- SPRITES GROUPS --- ###############
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

############## --- WORLD MAP --- ###############
world_data = []
for row in range(ROWS):
	r = [-1] * COLS # List of 150 entries of -1
	world_data.append(r)
# Load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)

############### --- GAME LOGIC -- ###############

run = True

while (run):

	clock.tick(FPS)

	if start_game == False:
		# Draw menu
		screen.fill(BG)
		# add buttons
		if start_button.draw(screen):
			start_game = True
		if exit_button.draw(screen):
			run = False
	else: 
		# update background
		draw_bg() 
		
		# Update and draw groups
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		decoration_group.update()
		item_box_group.update()
		exit_group.update()
		bullet_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		decoration_group.draw(screen)
		item_box_group.draw(screen)
		exit_group.draw(screen)
		# Draw qorld map
		world.draw()
		# Show player health
		health_bar.draw(player.health)
		# Show ammo
		draw_text(f'AMMO: ', font, WHITE, 10, 35)
		for x in range(player.ammo):
			screen.blit(bullet_img, (90 + (x * 10), 40))
		# Show grenades
		draw_text(f'GRENADES: ', font, WHITE, 10, 60)
		for x in range(player.grenades):
			screen.blit(grenade_img, (135 + (x * 15), 60))
			
		player.update()
		player.draw() # Draw player on the screen

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()


		# Update player actions
		if player.alive:
			screen_scroll, level_complete = player.move(moving_left, moving_right) # move the player
			bg_scroll -= screen_scroll
			# bg_scroll = max(0, bg_scroll)
			# CANDADO DE SEGURIDAD: Evita que el scroll sea negativo (la franja negra)
			if bg_scroll < 0:
				# Si el scroll se pasó de 0, devolvemos la diferencia al jugador
				# para que el personaje se mueva pero la cámara no
				player.hitbox.x += bg_scroll 
				bg_scroll = 0
			# CANDADO DE SEGURIDAD: Evita que el scroll pase del final del nivel
			max_scroll = (world.level_length * TILE_SIZE) - SCREEN_WIDTH
			if bg_scroll > max_scroll:
				player.hitbox.x += (bg_scroll - max_scroll)
				bg_scroll = max_scroll

			if shoot:
				player.update_action(4) # shoot 
				player.shoot() # Shoot
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
							player.rect.top, player.direction)
				grenade_group.add(grenade)
				player.grenades -= 1 # reduce the number of grenades
				grenade_thrown = True 
			elif player.in_air:
				player.update_action(2) # jump
			elif moving_left or moving_right:
				player.update_action(1) # running animation 
			else:
				player.update_action(0) # idle
			# check level completed
			if level_complete:
				# level += 1
				bg_scroll = 0
				world_data = reset_level()
				# Load in level data and create world
				with open(f'level{level}_data.csv', newline='') as csvfile:
					reader = csv.reader(csvfile, delimiter=',')
					for x, row in enumerate(reader):
						for y, tile in enumerate(row):
							world_data[x][y] = int(tile)

				world = World()
				player, health_bar = world.process_data(world_data)
		else:
			screen_scroll = 0
			if restart_button.draw(screen):
				bg_scroll = 0
				world_data = reset_level()
				# Load in level data and create world
				if level < MAX_LEVEL:
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)

					world = World()
					player, health_bar = world.process_data(world_data)

	for event in pygame.event.get():
		# quit game
		if event.type == pygame.QUIT:
			run = False
		# Keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a or event.key == pygame.K_LEFT:
				moving_left = True
			if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
				moving_right = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_q:
				grenade = True
			if (event.key == pygame.K_w or  event.key == pygame.K_UP) and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_ESCAPE:
				run = False
		# Keyboard button releases
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a or  event.key == pygame.K_LEFT:
				moving_left = False
			if event.key == pygame.K_d or  event.key == pygame.K_RIGHT:
				moving_right = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown = False

	pygame.display.update() # update window 

pygame.quit()