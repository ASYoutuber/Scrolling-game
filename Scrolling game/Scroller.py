import pygame
import os
import random
import csv
import button
from pygame import mixer

mixer.init()
pygame.init()

window_width = 800
window_height = int(window_width * 0.8)

window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption('Shooter')
icon = pygame.image.load(os.path.join("Assets/player/Idle/0.png"))
pygame.display.set_icon(icon)

clock = pygame.time.Clock()
fps = 60

gravity = 0.75
scroll_thresh = 200
tile_size = 40
rows = 16
cols = 150
tile_size = window_height // rows
tile_types = 21
window_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False
max_levels = 3

moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_throw = False

pygame.mixer.music.load(os.path.join("Assets/audio/music2.mp3"))
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)

jump_sound = pygame.mixer.Sound(os.path.join("Assets/audio/jump.wav"))
jump_sound.set_volume(0.5)

shoot_sound = pygame.mixer.Sound(os.path.join("Assets/audio/shot.wav"))
shoot_sound.set_volume(0.5)

grenade_sound = pygame.mixer.Sound(os.path.join("Assets/audio/grenade.wav"))
grenade_sound.set_volume(0.5)

image_list = []
for i in range(tile_types):
	image = pygame.image.load(os.path.join(f"Assets/tile/{i}.png"))
	image = pygame.transform.scale(image, (tile_size, tile_size))
	image_list.append(image)

grenade_img = pygame.image.load(os.path.join("Assets/icons/grenade.png")).convert_alpha()
health_box_img = pygame.image.load(os.path.join("Assets/icons/health_box.png")).convert_alpha()
grenade_box_img = pygame.image.load(os.path.join("Assets/icons/grenade_box.png")).convert_alpha()
bullet_box_img = pygame.image.load(os.path.join("Assets/icons/ammo_box.png")).convert_alpha()
bullet_img = pygame.image.load(os.path.join("Assets/icons/bullet show.png")).convert_alpha()

pine1_img = pygame.image.load(os.path.join("Assets/background/pine1.png")).convert_alpha()
pine2_img = pygame.image.load(os.path.join("Assets/background/pine1.png")).convert_alpha()
mountain_img = pygame.image.load(os.path.join("Assets/background/mountain.png")).convert_alpha()
sky_img = pygame.image.load(os.path.join("Assets/background/sky_cloud.png")).convert_alpha()

start_btn = pygame.image.load(os.path.join("Assets/start_btn.png")).convert_alpha()
exit_btn = pygame.image.load(os.path.join("Assets/exit_btn.png")).convert_alpha()
restart_btn = pygame.image.load(os.path.join("Assets/restart_btn.png")).convert_alpha()

item_boxes = {"Health" : health_box_img, "Grenade" : grenade_box_img, "Ammo" : bullet_box_img}

bg = (144, 201, 120)
red = (255, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
black = (0, 0, 0)
pink = (235, 65, 54)

font = pygame.font.SysFont("Times New Roman", 30)
font_ = pygame.font.SysFont("Times New Roman", 70)

def draw_text(text, font, text_col, x, y):
	image = font.render(text, True, text_col)
	window.blit(image, (x, y))

def draw_bg():
	width = sky_img.get_width()
	for i in range(5):
		window.blit(sky_img, ((i * width) - bg_scroll * 0.5, 0))
		window.blit(mountain_img, ((i * width) - bg_scroll * 0.6, window_height - mountain_img.get_height() - 300))
		window.blit(pine1_img, ((i * width) - bg_scroll * 0.7, window_height - pine1_img.get_height() - 150))
		window.blit(pine2_img, ((i * width) - bg_scroll * 0.8, window_height - pine2_img.get_height()))

def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	data = []
	for row in range(rows):
		r = [-1] * cols
		data.append(r)
	return data

class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
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
		self.action = 0
		self.update_time = pygame.time.get_ticks()

		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		self.flip_enemy = False
		
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			temp_list = []
			num_of_frames = len(os.listdir(f'Assets/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(os.path.join(f'Assets/{self.char_type}/{animation}/{i}.png')).convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()

	def update(self):
		self.update_animation()
		self.check_alive()
		if (self.shoot_cooldown > 0):
			self.shoot_cooldown -= 1


	def move(self, moving_left, moving_right):
		window_scroll = 0
		dx = 0
		dy = 0

		if (moving_left):
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if (moving_right):
			dx = self.speed
			self.flip = False
			self.direction = 1

		if (self.jump == True and self.in_air == False):
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		self.vel_y += gravity
		if (self.vel_y > 10):
			self.vel_y
		dy += self.vel_y

		for tile in world.obstacle_list:
			if (tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height)):
				dx = 0
				if (self.char_type == "enemy"):
					self.direction *= -1
					self.move_counter = 0

			if (tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height)):
				if (self.vel_y < 0):
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				elif (self.vel_y >= 0):
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom

		if (pygame.sprite.spritecollide(self, water_group, False)):
			self.health = 0
		
		level_complete = False
		if (pygame.sprite.spritecollide(self, exit_group, False)):
			level_complete = True

		if (self.rect.bottom > window_height):
			self.health = 0

		if (self.char_type == "player"):
			if (self.rect.left + dx < 0 or self.rect.right + dx > window_width):
				dx = 0

		self.rect.x += dx
		self.rect.y += dy

		if (self.char_type == "player"):
			if ((self.rect.right > window_width - scroll_thresh and bg_scroll < (world.level_length * tile_size) - window_width) or (self.rect.left < scroll_thresh and bg_scroll > abs(dx))):
				self.rect.x -= dx
				window_scroll = -dx
		return window_scroll, level_complete

	def shoot(self):
		if (self.shoot_cooldown == 0 and self.ammo > 0):
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo -= 1
			shoot_sound.play()

	def ai(self):
		if (self.alive and player.alive):
			if (self.idling == False and random.randint(1, 200) == 1):
				self.update_action(0)
				self.idling = True
				self.idling_counter = 50
			if (self.vision.colliderect(player.rect)):
				self.update_action(0)
				self.shoot()
			else:
				if (self.idling == False):
					if (self.direction == 1):
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)
					self.move_counter += 1
					
					self.vision.center = ((self.rect.centerx + 75 * self.direction), self.rect.centery)

					if (self.move_counter > tile_size):
						self.direction *= -1
						self.move_counter *= -1
				else:
					self.idling_counter -= 1
					if (self.idling_counter <= 0):
						self.idling = False
		self.rect.x += window_scroll

	def update_animation(self):
		animation_cooldown = 100
		self.image = self.animation_list[self.action][self.frame_index]
		if (pygame.time.get_ticks() - self.update_time > animation_cooldown):
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		if (self.frame_index >= len(self.animation_list[self.action])):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0

	def update_action(self, new_action):
		if (new_action != self.action):
			self.action = new_action
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()

	def check_alive(self):
		if (self.health <= 0):
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)

	def draw(self):
		window.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class World():
	def __init__(self):
		self.obstacle_list = []
	
	def process_data(self, data):
		self.level_length = len(data[0])
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if (tile >= 0):
					image = image_list[tile]
					image_rect = image.get_rect()
					image_rect.x = x * tile_size
					image_rect.y = y * tile_size
					tile_data = (image, image_rect)
					if (tile >= 0 and tile <= 8):
						self.obstacle_list.append(tile_data)
					elif (tile >= 9 and tile <= 10):
						water = Water(image, x * tile_size, y * tile_size)
						water_group.add(water)
					elif (tile >= 11 and tile <= 14):
						decoration = Decoration(image, x * tile_size, y * tile_size)
						decoration_group.add(decoration)
					elif (tile == 15):
						player = Soldier("player", x * tile_size, y * tile_size, 1.65, 5, 20, 5)
						health_bar = Health_Bar(10, 10, player.health, player.health)
					elif (tile == 16):
						enemy = Soldier("enemy", x * tile_size, y * tile_size, 1.65, 3, 20, 0)
						enemy_group.add(enemy)
					elif (tile == 17):
						item_box = Item_box("Ammo", x * tile_size, y * tile_size )
						item_box_group.add(item_box)
					elif (tile == 18):
						item_box = Item_box("Grenade", x * tile_size, y * tile_size)
						item_box_group.add(item_box)
					elif (tile == 19):
						item_box = Item_box("Health", x * tile_size, y * tile_size)
						item_box_group.add(item_box)
					elif (tile == 20):
						exit = Exit(image, x * tile_size, y * tile_size)
						exit_group.add(exit)
		return player, health_bar
	
	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += window_scroll
			window.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
	def __init__(self, image, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

	def update(self):
		self.rect.x += window_scroll

class Water(pygame.sprite.Sprite):
	def __init__(self, image, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))
	
	def update(self):
		self.rect.x += window_scroll

class Exit(pygame.sprite.Sprite):
	def __init__(self, image, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

	def update(self):
		self.rect.x += window_scroll

class Item_box(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

	def update(self):
		self.rect.x += window_scroll
		if (pygame.sprite.collide_rect(self, player)):
			if (self.item_type == "Health"):
				player.health += 25
				if (player.health > player.max_health):
					player.health = player.max_health
			elif (self.item_type == "Ammo"):
				player.ammo += 15
			elif (self.item_type == "Grenade"):
				player.grenades += 3
			self.kill()

class Health_Bar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health
	
	def draw(self, health):
		self.health = health

		ratio = self.health / self.max_health

		pygame.draw.rect(window, black, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(window, red, (self.x, self.y, 150, 20))
		pygame.draw.rect(window, green, (self.x, self.y, 150 * ratio, 20))

class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		self.rect.x += (self.direction * self.speed) + window_scroll
		if (self.rect.right < 0 or self.rect.left > window_width):
			self.kill()

		for tile in world.obstacle_list:
			if (tile[1].colliderect(self.rect)):
				self.kill()

		if (pygame.sprite.spritecollide(player, bullet_group, False)):
			if (player.alive):
				player.health -= 5
				self.kill()

		for enemy in enemy_group:
			if (pygame.sprite.spritecollide(enemy, bullet_group, False)):
				if (enemy.alive):
					enemy.health -= 25
					self.kill()

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
		self.vel_y += gravity
		dx = self.direction * self.speed
		dy = self.vel_y

		for tile in world.obstacle_list:
			if (tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height)):
				self.direction *= -1
				dx = self.direction * self.speed
		
		for tile in world.obstacle_list:
			if (tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height)):
				dx = 0

			if (tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height)):
				self.speed = 0
				if (self.vel_y < 0):
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				elif (self.vel_y >= 0):
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom

		self.rect.x += dx + window_scroll
		self.rect.y += dy

		self.timer -= 1
		if (self.timer <= 0):
			self.kill()
			grenade_sound.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			if (abs(self.rect.centerx - player.rect.centerx) < tile_size * 2 and abs(self.rect.centery - player.rect.centery) < tile_size * 2):
				player.health -= 50
			for enemy in enemy_group:
				if (abs(self.rect.centerx - enemy.rect.centerx) < tile_size * 2 and abs(self.rect.centery - enemy.rect.centery) < tile_size * 2):
					enemy.health -= 50

class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			explosion_img = pygame.image.load(os.path.join(f"Assets/explosion/exp{num}.png")).convert_alpha()
			explosion_img = pygame.transform.scale(explosion_img, (int(explosion_img.get_width() * scale), int(explosion_img.get_height() * scale)))
			self.images.append(explosion_img)
		self.index = 0
		self.image = self.images[self.index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0
	
	def update(self):
		self.rect.x += window_scroll
		explosion_speed = 4
		self.counter += 1
		
		if (self.counter >= explosion_speed):
			self.counter = 0
			self.index += 1
			if (self.index  >= len(self.images)):
				self.kill()
			else:
				self.image = self.images[self.index]

class Window_fade():
	def __init__(self, direction, color, speed):
		self.direction = direction
		self.color = color
		self.speed = speed
		self.fade_counter = 0

	def fade(self):
		fade_complete = False
		self.fade_counter += self.speed
		if (self.direction == 1):
			pygame.draw.rect(window, self.color, (0 - self.fade_counter, 0, window_width // 2, window_height))
			pygame.draw.rect(window, self.color, (window_width // 2 + self.fade_counter, 0, window_width, window_height))
			pygame.draw.rect(window, self.color, (0, 0 - self.fade_counter, window_width, window_height))
			pygame.draw.rect(window, self.color, (0, window_height // 2 + self.fade_counter, window_width, window_height))
		if (self.direction == 2):
			pygame.draw.rect(window, self.color, (0, 0, window_width, 0 + self.fade_counter))

		if (self.fade_counter >= window_width):
			fade_complete = True
		
		return fade_complete

start_fade = Window_fade(1, black, 4)
death_fade = Window_fade(2, pink, 4)

start_button = button.Button(window_width // 2 - 130, window_height // 2 - 150, start_btn, 1)
exit_button = button.Button(window_width // 2 - 110, window_height // 2 + 50, exit_btn, 1)
restart_button = button.Button(window_width // 2 - 100, window_height // 2 - 50, restart_btn, 2)

enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

world_data = []
for row in range(rows):
	r = [-1] * cols
	world_data.append(r)

with (open(os.path.join(f"Assets/levels/level{level}_data.csv"), newline = "") as csvfile):
	reader = csv.reader(csvfile, delimiter = ",")
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

run = True
while run:
	clock.tick(fps)

	if (start_game == False):
		window.fill(bg)
		if (start_button.draw(window)):
			start_game = True
			start_intro = True
		if (exit_button.draw(window)):
			run = False
	else:
		draw_bg()
		world.draw()

		health_bar.draw(player.health)

		draw_text("Ammo: ", font, white, 10, 35)
		for i in range(player.ammo):
			window.blit(bullet_img, (105 + (i * 10), 45))

		draw_text("Grenades: ", font, white, 10, 60)
		for i in range(player.grenades):
			window.blit(grenade_img, (135 + (i * 10), 70))

		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()

		bullet_group.draw(window)
		grenade_group.draw(window)
		explosion_group.draw(window)
		item_box_group.draw(window)
		decoration_group.draw(window)
		water_group.draw(window)
		exit_group.draw(window)

		if (start_intro == True):
			if (start_fade.fade()):
				start_intro = False
				start_fade.fade_counter = 0

		if (player.alive):
			if (shoot):
				player.shoot()
			elif (grenade and grenade_throw == False and player.grenades > 0):
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), player.rect.top, player.direction)
				grenade_group.add(grenade)
				grenade_throw = True
				player.grenades -= 1
			if (player.in_air):
				player.update_action(2)
			elif (moving_left or moving_right):
				player.update_action(1)
			else:
				player.update_action(0)
			window_scroll, level_complete = player.move(moving_left, moving_right)
			bg_scroll -= window_scroll
			if (level_complete):
				start_intro = True
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if (level <= max_levels):
					with (open(os.path.join(f"Assets/levels/level{level}_data.csv"), newline = "") as csvfile):
						reader = csv.reader(csvfile, delimiter = ",")
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)
			if (level_complete and level > max_levels):
				draw_text("You Win!", font_, white, (window_width // 2) - 150, window_height // 2)
				start_intro = False
				run = False

		else:
			window_scroll = 0
			if (death_fade.fade()):
				if (restart_button.draw(window)):
					death_fade.fade_counter = 0
					start_intro = True
					bg_scroll = 0
					world_data = reset_level()
					with (open(os.path.join(f"Assets/levels/level{level}_data.csv"), newline = "") as csvfile):
						reader = csv.reader(csvfile, delimiter = ",")
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)

	for event in pygame.event.get():
		if (event.type == pygame.QUIT):
			run = False

		if (event.type == pygame.KEYDOWN):
			if (event.key == pygame.K_LEFT):
				moving_left = True
			if (event.key == pygame.K_RIGHT):
				moving_right = True
			if (event.key == pygame.K_SPACE):
				shoot = True
			if (event.key == pygame.K_TAB):
				grenade = True
			if (event.key == pygame.K_UP and player.alive):
				player.jump = True
				jump_sound.play()
			if (event.key == pygame.K_ESCAPE):
				run = False

		if (event.type == pygame.KEYUP):
			if (event.key == pygame.K_LEFT):
				moving_left = False
			if (event.key == pygame.K_RIGHT):
				moving_right = False
			if (event.key == pygame.K_SPACE):
				shoot = False
			if (event.key == pygame.K_TAB):
				grenade = False
				grenade_throw = False

	pygame.display.update()
pygame.quit()