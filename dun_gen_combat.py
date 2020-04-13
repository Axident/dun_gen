from PySide.QtCore import *
from PySide.QtGui import *
import time

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