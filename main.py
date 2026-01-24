import pygame
import os

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

###############	--- FRAMERATE --- ###############
clock =  pygame.time.Clock()
FPS = 60


############### --- GAME VARIABLES --- ###############
GRAVITY = 0.75

############### --- ACTION VARIABLES --- ###############
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

############### --- IMAGES ---	###############

# Bullets
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()

# Grenades
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()

################ --- COLORS --- ###############
BG = (144, 201, 120)
RED = (255, 0, 0)

############### --- BACKGROUND --- ###############
def draw_bg():
	screen.fill(BG)
	pygame.draw.line(screen, RED, (0, 300), (SCREEN_WIDTH, 300))

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
		self.max_healt = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0 # index that indicates which animation I'm in
		self.update_time = pygame.time.get_ticks()

		# Load all animations for the player
		animation_types = ['Idle', 'Run', 'Jump' , 'Death']
		for animation in animation_types:
			temp_list = [] # temporary list to store animation groups
			# Count files in the folder
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha() 
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale))) # Scale the image since it's very small
				temp_list.append(img)
			self.animation_list.append(temp_list) # save temp_list in the animations list

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect() # rectangle around the image
		self.rect.center = (x, y) # place the rect in the position received as parameter

	def update(self):
		self.update_animation()
		self.check_alive()
		# Update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1

	def move(self, moving_left, moving_right):
		# Reset movement variables
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
		# Check collisions with floor
		if self.rect.bottom + dy > 300:
			dy = 300 - self.rect.bottom
			self.in_air = False

		# Update positions
		self.rect.x += dx
		self.rect.y += dy

	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo -= 1
		

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
		self.rect.x += (self.direction * self.speed)
		# Check if the bullet left the screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill() # clean memory
		# Collisions with other objects
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
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
		self.direction = direction
	
	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y
		# Check collisions with floor
		if self.rect.bottom + dy > 300:
			dy = 300 - self.rect.bottom
			self.speed = 0
		# Check if the grenade hits a wall
		if self.rect.right + dx < 0 or self.rect.left + dx > SCREEN_WIDTH:
			self.direction *= -1
			dx = self.direction * self.speed
		# Update grenade's position
		self.rect.x += dx
		self.rect.y += dy

		# Countdown for the explosion
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
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

############### --- SPRITES GROUPS --- ###############
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()

############### --- CHARACTERS --- ###############
player = Soldier('player', 200, 200, 3, 5, 20 , 5) # instance(player) from the Soldier class
enemy = Soldier('enemy', 400, 170, 3, 5, 20, 0) # instance(enemy) from the Soldier class

############### --- GAME LOGIC -- ###############

run = True

while (run):

	clock.tick(FPS)
	draw_bg() # Draw background

	player.update()
	player.draw() # Draw player on the screen
	enemy.update()
	enemy.draw()

	# Update and draw groups
	bullet_group.update()
	grenade_group.update()
	explosion_group.update()
	bullet_group.draw(screen)
	grenade_group.draw(screen)
	explosion_group.draw(screen)

	# Update player actions
	if player.alive:
		
		if shoot:
			player.shoot() # Shoot
		elif grenade and grenade_thrown == False and player.grenades > 0:
			grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
						player.rect.top, player.direction)
			grenade_group.add(grenade)
			player.grenades -= 1 # reduce the number of grenades
			grenade_thrown = True 
		if player.in_air:
			player.update_action(2) # jump
		elif moving_left or moving_right:
			player.update_action(1) # running animation 
		else:
			player.update_action(0) # idle
		player.move(moving_left, moving_right) # move the player

	for event in pygame.event.get():
		# quit game
		if event.type == pygame.QUIT:
			run = False
		# Keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_q:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
			if event.key == pygame.K_ESCAPE:
				run = False
		# Keyboard button releases
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown = False

	pygame.display.update() # update window 

pygame.quit()