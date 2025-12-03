### Author: kristen. 
### please don't use it for commercial purpose. indicating the source when reprinting
### 1553702482@qq.com

import pygame
import random
import math
import time
from enum import Enum

# 定义游戏常量
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 30  
BATTLE_FIELD_SIZE = 20  
MARGIN = (WIDTH - BATTLE_FIELD_SIZE * GRID_SIZE) // 2
CELL_SIZE = GRID_SIZE
FPS = 60
REFRESH_RATE = 0.1  

class UnitType(Enum):
    INFANTRY = 0
    ARCHER = 1
    CAVALRY = 2
    ARTILLERY = 3

UNIT_PROPERTIES = {
    UnitType.INFANTRY: {
        "name": "步兵",
        "health": 100,
        "damage": 10,
        "range": 1,
        "speed": 1,
    },
    UnitType.ARCHER: {
        "name": "弓箭手",
        "health": 70,
        "damage": 15,
        "range": 3,
        "speed": 1,
    },
    UnitType.CAVALRY: {
        "name": "骑兵",
        "health": 80,
        "damage": 15,
        "range": 1,
        "speed": 2,
    },
    UnitType.ARTILLERY: {
        "name": "炮兵",
        "health": 120,
        "damage": 25,
        "range": 5,
        "speed": 0.5,
    }
}

class Unit:
    def __init__(self, x, y, team, unit_type, unit_id):
        self.x = x
        self.y = y
        self.team = team  
        self.type = unit_type
        self.id = unit_id
        self.health = UNIT_PROPERTIES[unit_type]["health"]
        self.damage = UNIT_PROPERTIES[unit_type]["damage"]
        self.range = UNIT_PROPERTIES[unit_type]["range"]
        self.speed = UNIT_PROPERTIES[unit_type]["speed"]
        self.in_range = False
        self.target = None
        self.moving = False
        self.attack_cooldown = 0
        self.attack_cooldown_max = 1  
        self.target_refresh_counter = 0  

    def update(self, enemies):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        if self.health <= 0:
            return False
        
        if self.target and self.in_range and self.attack_cooldown == 0:
            if self.target.health <= 0:
                self.find_new_target(enemies)
            else:
                self.target.health -= self.damage
                self.attack_cooldown = self.attack_cooldown_max / REFRESH_RATE
                return True
            
        if self.target_refresh_counter <= 0 or not self.target or self.target.health <= 0:
            self.find_new_target(enemies)
            self.target_refresh_counter = 3 * REFRESH_RATE  
        else:
            self.target_refresh_counter -= 1
            
        if self.target:
            target_x, target_y = self.target.x, self.target.y
            
            distance = math.sqrt((self.x - target_x) ** 2 + (self.y - target_y) ** 2)
            
            if distance <= self.range:
                self.in_range = True
            else:
                self.in_range = False
                
                dx = target_x - self.x
                dy = target_y - self.y
                
                norm = math.sqrt(dx ** 2 + dy ** 2)
                if norm > 0:
                    dx = dx / norm * self.speed * REFRESH_RATE
                    dy = dy / norm * self.speed * REFRESH_RATE
                
                self.x += dx
                self.y += dy
        
        return True
    
    def find_new_target(self, enemies):
        if not enemies:
            self.target = None
            return
            
        min_distance = float('inf')
        closest_enemy = None
        
        for enemy in enemies:
            if enemy.health <= 0:
                continue
                
            distance = abs(self.x - enemy.x) + abs(self.y - enemy.y)  
            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy
                
        self.target = closest_enemy

    def draw(self, screen, team_colors=((255, 0, 0), (0, 0, 255))):
        # 根据阵营选择颜色
        team_color = team_colors[self.team]
        
        # 根据兵种类型选择绘制形状
        if self.type == UnitType.INFANTRY:
            # 步兵：圆形
            pygame.draw.circle(screen, team_color, 
                             (self.x * GRID_SIZE + MARGIN + GRID_SIZE // 2, 
                              self.y * GRID_SIZE + GRID_SIZE // 2), 
                             GRID_SIZE // 2 - 2)
        elif self.type == UnitType.ARCHER:
            # 弓箭手：三角形
            pygame.draw.polygon(screen, team_color, 
                              [(self.x * GRID_SIZE + MARGIN + GRID_SIZE // 2, self.y * GRID_SIZE + 10),
                               (self.x * GRID_SIZE + MARGIN + GRID_SIZE - 10, self.y * GRID_SIZE + GRID_SIZE - 10),
                               (self.x * GRID_SIZE + MARGIN + 10, self.y * GRID_SIZE + GRID_SIZE - 10)])
        elif self.type == UnitType.CAVALRY:
            # 骑兵：正方形
            pygame.draw.rect(screen, team_color, 
                           (self.x * GRID_SIZE + MARGIN + 5, self.y * GRID_SIZE + 5, 
                            GRID_SIZE - 10, GRID_SIZE - 10))
        elif self.type == UnitType.ARTILLERY:
            # 炮兵：六边形
            center_x = self.x * GRID_SIZE + MARGIN + GRID_SIZE // 2
            center_y = self.y * GRID_SIZE + GRID_SIZE // 2
            size = GRID_SIZE // 3
            points = []
            for i in range(6):
                angle = 60 * i * math.pi / 180
                points.append((center_x + size * math.cos(angle), 
                              center_y + size * math.sin(angle)))
            pygame.draw.polygon(screen, team_color, points)
        
        # 绘制生命值条
        health_ratio = self.health / UNIT_PROPERTIES[self.type]["health"]
        health_width = GRID_SIZE * health_ratio
        health_rect = pygame.Rect(self.x * GRID_SIZE + MARGIN, 
                                 self.y * GRID_SIZE - 5, 
                                 health_width, 5)
        pygame.draw.rect(screen, (0, 255, 0) if health_ratio > 0.5 else (255, 0, 0), health_rect)



class Game:
    def __init__(self):
        self.units = []
        self.team0 = []
        self.team1 = []
        self.last_update = 0
        self.game_over = False
        self.winner = None
        self.waiting_for_start = True  # 添加等待开始状态
        
    def initialize_units(self):
        self.units = []
        self.team0 = []
        self.team1 = []
        
        for i in range(random.randint(10, 20)):
            unit_type = random.choice(list(UnitType))
            unit = Unit(random.randint(0, BATTLE_FIELD_SIZE-1), 0, 0, unit_type, i)
            self.units.append(unit)
            self.team0.append(unit)
        
        for i in range(random.randint(10, 20)):
            unit_type = random.choice(list(UnitType))
            unit = Unit(random.randint(0, BATTLE_FIELD_SIZE-1), BATTLE_FIELD_SIZE-1, 1, unit_type, i)
            self.units.append(unit)
            self.team1.append(unit)
        
        for unit in self.units:
            if unit.team == 0:
                unit.find_new_target(self.team1)
            else:
                unit.find_new_target(self.team0)
        
    def update(self):
        if self.waiting_for_start:
            return False  # 如果处于等待开始状态，不更新游戏逻辑
        
        current_time = time.time()
        
        if current_time - self.last_update >= REFRESH_RATE:
            self.last_update = current_time
            
            for unit in self.units:
                if not unit.update(self.team1 if unit.team == 0 else self.team0):
                    if unit in self.team0:
                        self.team0.remove(unit)
                    if unit in self.team1:
                        self.team1.remove(unit)
                    if unit in self.units:
                        self.units.remove(unit)
            
            if not self.team0:
                self.game_over = True
                self.winner = "Blue Team"
            elif not self.team1:
                self.game_over = True
                self.winner = "Red Team"
            
            return True
        
        return False
    
    def draw(self, screen):
        screen.fill((255, 255, 255))
        
        for x in range(BATTLE_FIELD_SIZE):
            for y in range(BATTLE_FIELD_SIZE):
                rect = pygame.Rect(x * GRID_SIZE + MARGIN, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)
        
        for unit in self.units:
            unit.draw(screen)
        
        if self.waiting_for_start:
            font = pygame.font.SysFont(None, 36)
            start_text = font.render("press S to start", True, (0, 0, 0))
            screen.blit(start_text, (MARGIN, BATTLE_FIELD_SIZE * GRID_SIZE // 2 - 30))
        elif not self.game_over:
            team0_count = len([u for u in self.team0 if u.health > 0])
            team1_count = len([u for u in self.team1 if u.health > 0])
            
            font = pygame.font.SysFont(None, 24)
            team0_text = font.render(f"Red Team: {team0_count} units", True, (255, 0, 0))
            team1_text = font.render(f"Blue Team: {team1_count} units", True, (0, 0, 255))
            screen.blit(team0_text, (MARGIN, BATTLE_FIELD_SIZE * GRID_SIZE + 10))
            screen.blit(team1_text, (MARGIN, BATTLE_FIELD_SIZE * GRID_SIZE + 40))
        else:
            big_font = pygame.font.SysFont(None, 36)
            winner_text = big_font.render(f"Game Over! {self.winner} wins!", True, (0, 0, 0))
            screen.blit(winner_text, (MARGIN, BATTLE_FIELD_SIZE * GRID_SIZE // 2 - 30))
            
            font = pygame.font.SysFont(None, 24)
            restart_text = font.render("press R to restart", True, (0, 0, 0))
            screen.blit(restart_text, (MARGIN, BATTLE_FIELD_SIZE * GRID_SIZE // 2 + 20))
        
        info_text = font.render("Unit Types: Infantry (circle) - Archer (triangle) - Cavalry (square) - Artillery (hexagon)", True, (0, 0, 0))
        screen.blit(info_text, (MARGIN, BATTLE_FIELD_SIZE * GRID_SIZE + 70))
        
        pygame.display.flip()
    
    def handle_events(self, screen):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.__init__()
                    self.initialize_units()
                    self.draw(screen)
                elif event.key == pygame.K_s and self.waiting_for_start:
                    self.waiting_for_start = False
        
        return True
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Battle Simulation")
    clock = pygame.time.Clock()
    game = Game()
    game.initialize_units()
    game.draw(screen)  # 初始绘制
    
    running = True
    
    while running:
        running = game.handle_events(screen)  # 传递 screen 参数
        if not game.waiting_for_start:  # 只有在游戏开始后才更新游戏逻辑
            game.update()
        game.draw(screen)
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
    
