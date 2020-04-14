from PySide.QtCore import *
from PySide.QtGui import *
import time
import random

class Projectile(object):
    def __init__(self, location, tile_color, direction):
        self.direction = direction
        self.tile_color = tile_color
        #self.color = (0,0,0)
        self.location = location
        
    def move(self):
        next_row, next_col = self.location
        if self.direction == 'north':
            next_row -= 1
        elif self.direction == 'south':
            next_row += 1
        elif self.direction == 'west':
            next_col -= 1
        elif self.direction == 'east':
            next_col += 1
        self.location = [next_row, next_col]

class BulletTimeWorker(QThread):
    status = Signal(object)
    finished = Signal(object)

    def __init__(self, data, parent=None):
        QThread.__init__(self, parent)
        self.data = data
        self.parent = parent
        self.projectiles = []
        
    def add(self, location, tile_color, direction):
        bullet = Projectile(location, tile_color, direction)
        self.projectiles.append(bullet)
        
    def run(self):
        while len(self.projectiles):
            time.sleep(.05)
            new_projectiles = []
            for projectile in self.projectiles:
                projectile.move()
                r,c = projectile.location
                cell = self.data[r][c]
                if cell.color == projectile.tile_color:
                    new_projectiles.append(projectile)
            self.projectiles = new_projectiles
            self.status.emit(self.projectiles)
        self.finished.emit(None)
        
    def stop(self):
        self.terminate()

class Monster(object):
    def __init__(self, data):
        self.data = data
        self.direction = None
        
        location = self.set_start_location()
        self.location = location
        self.next_location = location
        self.desired_location = location
        self.current_path = []
        self.color = (200,200,200)
        self.alive = True
        
    def __str__(self):
        return 'beast @ %s direction: %s, headed_to: %s' % (self.location, self.direction, self.desired_location)
        
    def set_start_location(self):
        halls = []
        for r in range(0,99):
            for c in range(0,99):
                cell = self.data[r][c]
                if cell.space_type == 'hall':
                    halls.append(cell)
        i = random.randint(0, len(halls)-1)
        self.current_space_type = halls[i].space_type
        return halls[i].location
        
    def move(self):
        next_row, next_col = self.location
        if len(self.current_path) == 0:
            #print "beast reached goal"
            directions = []
            item = self.data[next_row][next_col]
            for d in ['north', 'south', 'east', 'west']:
                value = getattr(item, d)
                if value:
                    directions.append(d)
            if directions and random.randint(0,1):
                i = 0
                if len(directions)>1:
                    i = random.randint(0, len(directions)-1)
                direction = directions[i]
                if direction == 'north':
                    next_row -= 1
                elif direction == 'south':
                    next_row += 1
                elif direction == 'west':
                    next_col -= 1
                elif direction == 'east':
                    next_col += 1
                self.desired_location = [next_row, next_col]
                self.current_path = [[next_row, next_col]]
            else:
                self.new_desired_location()
        cur_row, cur_col = self.location
        path_row, path_col = self.current_path.pop(0)
        if path_row < cur_row:
            self.direction = 'north'
        if path_row > cur_row:
            self.direction = 'south'
        if path_col > cur_col:
            self.direction = 'east'
        if path_col < cur_col:
            self.direction = 'west'
        self.location = [path_row, path_col]
        item = self.data[path_row][path_col]
        self.current_space_type = item.space_type
        self.color = item.color
            
    def new_desired_location(self):
        #print 'setting new desired location'
        desired_locations = set()
        row, column = self.location
        item = self.data[row][column]
        paths = []
        for direction in ['north','south','west','east']:
            path = self.look(row, column, direction, path = [[row, column]])
            paths.append(path)
            if len(path) > 2:
                for cell in range(2,len(path)):
                    branch = path[:cell]
                    b_row, b_col = path[cell-1]
                    if direction in ['north', 'south']:
                        for sub_d in ['east', 'west']:
                            test = self.look(b_row, b_col, sub_d, path=[])
                            if len(test):
                                r, c = test[-1]
                                last_item = self.data[r][c]
                                for d in ['north', 'south', 'east', 'west']:
                                    if getattr(last_item, d):
                                        test = branch + test
                                        paths.append(test)
                    if direction in ['east', 'west']:
                        for sub_d in ['north', 'south']:
                            test = self.look(b_row, b_col, sub_d, path=[])
                            if len(test):
                                r, c = test[-1]
                                last_item = self.data[r][c]
                                for d in ['north', 'south', 'east', 'west']:
                                    if getattr(last_item, d):
                                        test = branch + test
                                        paths.append(test)
        i = 0
        if len(paths)>1:
            i = random.randint(0, len(paths)-1)
        self.current_path = paths[i]
        self.desired_location = self.current_path[-1]
        #print 'chosen path:',self.current_path
            
    def look(self, row, column, direction, path = []):
        next_row = row
        next_col = column
        if 'north' in direction:
            next_row -= 1
        elif 'south' in direction:
            next_row += 1
        elif 'west' in direction:
            next_col -= 1
        elif 'east' in direction:
            next_col += 1
        if next_row<=0 or next_row>=99 or next_col<=0 or next_col>=99:
            return path
        next_item = self.data[next_row][next_col]
        if next_item.color == self.color:
            path.append([next_row, next_col])
            for d in ['north', 'south', 'east', 'west']:
                if getattr(next_item, d):
                    return path
            self.look(next_row, next_col, direction, path=path)
        return path

class WanderWorker(QThread):
    status = Signal(object)
    finished = Signal(object)

    def __init__(self, data, parent=None):
        QThread.__init__(self, parent)
        self.data = data
        self.parent = parent
        self.beasts = []
        
    def add(self, location=None):
        monster = Monster(self.data)
        self.beasts.append(monster)
        
    def run(self):
        while len(self.beasts):
            time.sleep(.5)
            new_beasts = []
            for beast in self.beasts:
                beast.move()
                r,c = beast.location
                if beast.alive:
                    new_beasts.append(beast)
            self.beasts = new_beasts
            self.status.emit(self.beasts)
        self.finished.emit(None)
        
    def stop(self):
        self.terminate()