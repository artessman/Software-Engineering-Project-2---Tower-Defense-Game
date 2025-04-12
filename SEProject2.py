
import json
from tkinter import SE
import pygame as pg
import math
import constants as c

##############################################
#  GAME CLASSES
##############################################

class Enemy(pg.sprite.Sprite):
    def __init__(self, path, health, speed, reward, image, sprite_sheet):
        super().__init__()
        self.path = path  
        self.OG_image = image
        self.sprite_sheet = sprite_sheet  # The sprite sheet
        self.angle = 0
        self.image = pg.transform.rotate(self.OG_image, self.angle)
        self.rect = self.image.get_rect()
        self.health = health
        self.speed = speed
        self.reward = reward
        self.current_pos = list(path[0])  # List to allow for updates
        self.target_index = 1
        self.alive = True
        self.current_frame = 0  # Used to keep track of the current walking animation frame
        self.animation_speed = 0.1  # Adjust this value to change animation speed
        self.animation_timer = 0  # Timer to handle frame switching

    def update(self):
        self.move()
        self.rotate()
        self.animate_walk()  

    def move(self):
        if self.target_index < len(self.path):
            target = self.path[self.target_index]
            dx = target[0] - self.current_pos[0]
            dy = target[1] - self.current_pos[1]
            distance = (dx**2 + dy**2) ** 0.5  
            if distance < self.speed:  # Prevent overshooting
                self.current_pos = list(target)
                self.target_index += 1
            else:
                self.current_pos[0] += (dx / distance) * self.speed
                self.current_pos[1] += (dy / distance) * self.speed
            
            self.rect.center = (int(self.current_pos[0]), int(self.current_pos[1]))  # Update sprite position
        else:
            self.kill()  # Enemy reached the end

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            self.kill()  # Remove sprite from the group

    def rotate(self):
        if self.target_index < len(self.path):  # Ensure there's a target
            target = self.path[self.target_index]
            dx = target[0] - self.current_pos[0]
            dy = target[1] - self.current_pos[1]
            self.angle = math.degrees(math.atan2(-dy, dx))  # Calculate angle

            # Rotate image and update rectangle
            self.image = pg.transform.rotate(self.OG_image, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)

    def animate_walk(self):
        # Determine the movement direction
        if self.target_index < len(self.path):
            target = self.path[self.target_index]
            dx = target[0] - self.current_pos[0]
            dy = target[1] - self.current_pos[1]

            if abs(dx) > abs(dy):  # Moving left or right
                if dx > 0:
                    direction = 'right'
                else:
                    direction = 'left'
            else:  # Moving up or down
                if dy > 0:
                    direction = 'down'
                else:
                    direction = 'up'
            
            # Update the animation frame
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame += 1
                if self.current_frame >= 4:  # There are 4 frames per animation (Up, Down, Left, Right)
                    self.current_frame = 0

            # Pick the correct row based on the direction
            if direction == 'down':
                row = 0  # First row for 'down'
            elif direction == 'left':
                row = 1  # Second row for 'left'
            elif direction == 'right':
                row = 2  # Third row for 'right'
            elif direction == 'up':
                row = 3  # Fourth row for 'up'

            
            self.image = self.sprite_sheet.subsurface((self.current_frame * 72, row * 72, 72, 72 ))

            
            self.rect = self.image.get_rect(center=self.rect.center)

class FastEnemy(Enemy):
    def __init__(self, path, image, sprite_sheet):
        super().__init__(path, health=50, speed=3, reward=10, image = image, sprite_sheet=sprite_sheet)

class TankEnemy(Enemy):
    def __init__(self, path, image,  sprite_sheet):
        super().__init__(path, health=200, speed=1, reward=30, image = image, sprite_sheet=sprite_sheet)

class SwarmEnemy(Enemy):
    def __init__(self, path, image, sprite_sheet):
        super().__init__(path, health=20, speed=2, reward=5, image = image, sprite_sheet=sprite_sheet)

class World():
  def __init__(self, data, map_image):
    self.tile_map = []
    self.waypoints = []
    self.level_data = data
    self.image = map_image

  def process_data(self):
    #look through data to extract relevant info
    for layer in self.level_data["layers"]:
      if layer["name"] == "Tile Layer 1":
          self.tile_map = layer["data"]
      if layer["name"] == "Waypoints":
        for obj in layer["objects"]:
          waypoint_data = obj["polyline"]
          self.process_waypoints(waypoint_data)

  def process_waypoints(self, data):
    #iterate through waypoints to extract individual sets of x and y coordinates
    for point in data:
      temp_x = point.get("x")
      temp_y = point.get("y")
      self.waypoints.append((temp_x + 222.67, temp_y)) #adjusted for absolute path

  def draw(self, surface):
    surface.blit(self.image, (0, 0))

class Tower(pg.sprite.Sprite):
    def __init__(self, tower_sheet, weapon_sheet, projectile, tile_x, tile_y):
        super().__init__()
        #pos variables 
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.x = (self.tile_x + 0.5) * c.TILE_SIZE 
        self.y = (self.tile_y + 0.5) * c.TILE_SIZE
        self.tower_level = 0  # Start at level 0
        self.weapon_offsets = {  #by level
            0: (0, -10),
            1: (0, -15),
            2: (0, -20)
        }
        #range
        self.range = 150
        self.selected = False
        self.target = None
        #cooldowns
        self.cooldown = 1500
        self.lastfired = pg.time.get_ticks()


        #animation variavbles: 
        
        self.tower_sheet = tower_sheet
        self.weapon_sheet = weapon_sheet
        self.projectile = projectile
        self.animation_list = self.load_images()
        self.frame_index = 0
        self.update_time =  pg.time.get_ticks()

        self.angle = 90
        self.OG_weapon_image = self.animation_list[self.frame_index]
        self.rot_weapon_image = pg.transform.rotate(self.OG_weapon_image, self.angle)

        self.image = self.tower_sheet.subsurface((self.tower_level * 64, 0, 64, 128))
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        #range indicator
        self.range_image = pg.Surface((self.range * 2, self.range * 2))
        self.range_image.fill((0,0,0))
        self.range_image.set_colorkey((0,0,0))
        pg.draw.circle(self.range_image, "grey100", (self.range, self.range), self.range) 
        self.range_image.set_alpha(100)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center

    def upgrade(self):
        if self.tower_level < 2:
            self.tower_level += 1
            self.image = self.tower_sheet.subsurface((self.tower_level * 64, 0, 64, 128))
            self.rect = self.image.get_rect(center=(self.x, self.y))
    def load_images(self):
        #extract images form spritew sheet
        size =  self.weapon_sheet.get_height()
        animation_list = []
        for x in range(6):#six frames
             temp_img = self.weapon_sheet.subsurface(x * size, 0 , size, size)
             animation_list.append(temp_img)
        return animation_list
    def play_animation(self):
        #update img
        self.OG_weapon_image = self.animation_list[self.frame_index]
        #check if enough time has passed since last frame
        if pg.time.get_ticks() - self.update_time > 15: #miliseconds
            self.update_time =  pg.time.get_ticks()
            self.frame_index += 1
            #check if the index is out of bounds
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
                #record time
                self.lastfired = pg.time.get_ticks()
                self.target = None #rest target after aniamtion to look for new enemy
    def update(self, enemy_group):
        #if target found play animation
        if self.target:
            self.play_animation()
        else:
            #search for new target after cooldown
            if pg.time.get_ticks() - self.lastfired > self.cooldown:
                self.select_target(enemy_group)
    def draw(self, surface):
        #self.rot_weapon_image = pg.transform.rotate(self.OG_weapon_image, self.angle -90)
        #self.rect = self.rot_weapon_image.get_rect()
        #self.rect.center = (self.x, self.y)

        # Draw tower base
        surface.blit(self.image, self.rect)

        #draw range of tower
        if self.selected:
            surface.blit(self.range_image, self.range_rect)

        # Draw weapon animation frame centered on the tower
        offset = self.weapon_offsets.get(self.tower_level, (0, 0)) #indexing the offeset by tower level
        self.rot_weapon_image = pg.transform.rotate(self.OG_weapon_image, self.angle -90)
        weapon_rect = self.rot_weapon_image.get_rect(center=(self.rect.centerx + offset[0],self.rect.centery + offset[1]))
        surface.blit(self.rot_weapon_image, weapon_rect)
    def select_target(self, enemy_group):
        #find closest enemy (euclidian dist)
        x_dist = 0
        y_dist = 0 
        for enemy in enemy_group:
            x_dist = enemy.current_pos[0] - self.x
            y_dist = enemy.current_pos[1] - self.y
            dist = (x_dist**2 + y_dist**2)**.5

            if dist < self.range:
                self.target = enemy
                self.angle = math.degrees(math.atan2(-y_dist, x_dist))
                



class Button():
  def __init__(self, x, y, image, single_click):
    self.image = image
    self.rect = self.image.get_rect()
    self.rect.topleft = (x, y)
    self.clicked = False
    self.single_click = single_click

  def draw(self, surface):
    action = False
    #get mouse position
    pos = pg.mouse.get_pos()

    #check mouseover and clicked conditions
    if self.rect.collidepoint(pos):
      if pg.mouse.get_pressed()[0] == 1 and self.clicked == False:
        action = True
        #if button is a single click type, then set clicked to True
        if self.single_click:
          self.clicked = True

    if pg.mouse.get_pressed()[0] == 0:
      self.clicked = False

    #draw button on screen
    surface.blit(self.image, self.rect)

    return action


##############################################
#  GAME FUNCTIONS
##############################################
        
def create_tower(mousePos):
        #tiles 
        mouse_tile_x = mousePos[0] // c.TILE_SIZE
        mouse_tile_y = mousePos[1] // c.TILE_SIZE

        mouse_tile_num =(mouse_tile_y *c.COLS) + mouse_tile_x 
        #check for grass
        if world.tile_map[mouse_tile_num] == 119:
            spacefree = True
            for t in tower_group:
                if (mouse_tile_x, mouse_tile_y) == (t.tile_x, t.tile_y):
                    spacefree = False
            if spacefree:
                tower = Tower(tower1_image, tower1_weapon, tower1_projectile, mouse_tile_x, mouse_tile_y)
                tower_group.add(tower)

def get_selected_tower(mousePos):
        #tiles 
        mouse_tile_x = mousePos[0] // c.TILE_SIZE
        mouse_tile_y = mousePos[1] // c.TILE_SIZE

        for tower in tower_group:
            if (mouse_tile_x, mouse_tile_y) == (tower.tile_x, tower.tile_y):
                return tower

        return None #if no tower

def clear_tower_selection():
    for tower in tower_group:
        tower.selected = False
       

        
# pygame setup
pg.init()
screen = pg.display.set_mode((c.SCREEN_WIDTH + c.SIDE_PANNEL, c.SCREEN_HEIGHT))   
clock = pg.time.Clock()

################
# game variables
################

placing_tower = False
selected_tower = None

#############
# load images
#############

# map
map_image = pg.image.load('images/sprites/medieval_level.png').convert_alpha()
# tower_images 
tower1_image = pg.image.load('images/sprites/TowersILike/Towers/Tower 01.png').convert_alpha()
tower1_weapon = pg.image.load('images/sprites/TowersILike/Weapons/Tower 06/Spritesheets/Tower 06 - Level 01 - Weapon.png').convert_alpha()
tower1_projectile = pg.image.load('images/sprites/TowersILike/Weapons/Tower 06/Spritesheets/Tower 06 - Level 01 - Projectile.png').convert_alpha()
#shop buttons
buy_tower = pg.image.load('images/sprites/Shopimg/buy_turret.png').convert_alpha()
cancel = pg.image.load('images/sprites/Shopimg/cancel.png').convert_alpha()


tower1_shopImg = tower1_image.subsurface((0 * 64, 0, 64, 128))



# Load Level Json data
with open('map.tmj') as file:
    world_data = json.load(file)

#create world
world = World(world_data,map_image)
world.process_data()
#Create enemy group
enemy_group = pg.sprite.Group()

#Create tower group
tower_group = pg.sprite.Group()

tower_button = Button(c.SCREEN_WIDTH + 30, 120, buy_tower, True)
cancel_button = Button(c.SCREEN_WIDTH + 30, 180, cancel, True)

# Create a proper path and enemy instance
print(world.waypoints)

test_sheet = pg.image.load('images/sprites/test/48x48/Char_002.png').convert_alpha()

# Create an enemy and add it to the group
enemy = FastEnemy(world.waypoints, cancel, test_sheet)
enemy_group.add(enemy)

#clicks = [] #for getting path for different maps
# Game loop
run = True
while run:
 
    clock.tick(c.FPS)
    ################
    # Update
    ################

    enemy_group.update()
    tower_group.update(enemy_group)
    #highlight selected turret
    if selected_tower:
        selected_tower.selected = True

    ################
    # Draw
    ################
    
    screen.fill("grey100")
    #map
    world.draw(screen)
    #enemies
    enemy_group.draw(screen)
    #towers
    for tower in tower_group:
        tower.draw(screen)
    #shop
    if tower_button.draw(screen):
        print('clicked tower')
        placing_tower = True
        #if placing tower then show the cancel button
    if placing_tower == True:

        cursor_rect = tower1_shopImg.get_rect()
        cursor_pos = pg.mouse.get_pos()
        cursor_rect.center = cursor_pos
        if cursor_pos[0] <= c.SCREEN_WIDTH:
            screen.blit(tower1_shopImg, cursor_rect)
        if cancel_button.draw(screen):
            print('clicked cancel')
            placing_tower = False

    #click = pg.mouse.get_pos()
    # Event handler
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button ==1:
            mousePos = pg.mouse.get_pos()
            #CHECK THAT THE MOUSE CLICK IS ON THE GAME AREA
            if mousePos[0] < c.SCREEN_WIDTH and mousePos[1] < c.SCREEN_HEIGHT:
                #clear selected tower
                selected_tower = None
                clear_tower_selection()
                if placing_tower == True:
                    create_tower(mousePos)
                else:
                    selected_tower = get_selected_tower(mousePos)
        ''' Code to get cords for the path
        if event.type == pg.MOUSEBUTTONDOWN:
            clicks.append(click)
            pg.draw.circle(screen, (255,0,0), (click), 5,0)
        '''

    pg.display.flip()


#print(clicks)
pg.quit()
