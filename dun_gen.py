try:
    from PySide.QtCore import *
    from PySide.QtGui import *
except:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    
from customLoader import loadUi
import os
import re
import time
import sys
import random
from functools import partial
from PIL import Image, ImageDraw, ImageFont

here = os.path.dirname(__file__)
from dun_gen_builder import *
from dun_gen_combat import *


class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        
        loadUi(r"%s\dun_gen.ui" % here, self)
        self.map_scene = QGraphicsScene(self)
        self.map_scene.setSceneRect(10, 10, 1010, 1010)
        self.map_view.setScene(self.map_scene)
        self.map_view.setSceneRect(0, 0, 1020, 1020)
        self.current_location = [50, 50]
        self.current_direction = None
        self.data = []
        self.rooms = {}
        self.halways = {}
        self.rooms_known = {}
        self.halls_known = {}
        self.cells_known = []
        self.show_secrets = False
        self.secret_range = 1
        self.exit_door = ()
        
        self.kills = 0
        self.monsters = []
        self.projectiles = []
        self.current_visible = []
        self.alive = True
        self.paused = True
        self.exits_found = 0
        self.extra_lives = 0
        self.spent_lives = 0
        self.deaths = 0
        self.bonus_points = 0
        self.myself = None
        
        self.bullet_timer = BulletTimeWorker(parent=self)
        self.bullet_timer.status.connect(self.update_projectiles)
        self.monster_timer = WanderWorker(self.data, parent=self)
        self.monster_timer.status.connect(self.update_monsters)
        self.map_builder = MapBuilderWorker(parent=self)
        self.map_builder.status.connect(self.update_image)
        self.map_builder.finished.connect(self.save_map)
        self.go_again.clicked.connect(self.respawn)
        self.cheat_map.clicked.connect(self.toggle_cheat_map)
        self.doit.clicked.connect(self.gen_map)

        self.map_image = None
        self.known_image = None

        self.installEventFilter(self)
        self.map_view.installEventFilter(self)

    def eventFilter(self, widget, event):
        if widget.objectName() == 'map_view':
            if event.type() == QEvent.Type.Wheel:
                factor = 1.15
                if event.angleDelta().y() < 0:
                    factor = 1.0 / factor
                self.map_view.scale(factor, factor)
                if self.myself:
                    self.map_view.centerOn(self.myself)
                #self.map_view.update()
                return True
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_N:
                print('generating new map')
                self.gen_map()
                return True
            if not self.alive:
                return False
            if event.key() == Qt.Key_W:
                #print('moving north')
                self.move('north')
            if event.key() == Qt.Key_A:
                #print('moving west')
                self.move('west')
            if event.key() == Qt.Key_S:
                #print('moving south')
                self.move('south')
            if event.key() == Qt.Key_D:
                #print('moving east')
                self.move('east')
            if event.key() == Qt.Key_P:
                #print('pause pressed')
                self.pause()
            if event.key() == Qt.Key_Space:
                #print('firing %s' % self.current_direction)
                self.fire()
            return True      
        return False      
        
    def closeEvent(self, event):
        if self.map_builder.isRunning():            
            self.map_builder.stop()
        if self.monster_timer.isRunning():            
            self.monster_timer.stop()
        if self.bullet_timer.isRunning():            
            self.bullet_timer.stop()

    def respawn(self):
        self.alive = True
        self.spent_lives += 1
        self.set_known()
            
    def pause(self):
        if self.paused:
            self.paused = False
            self.doit.setEnabled(False)
            self.cheat_map.setEnabled(False)
            self.cheat_monsters.setEnabled(False)
        else:
            self.paused = True
            self.doit.setEnabled(True)
            self.cheat_map.setEnabled(True)
            self.cheat_monsters.setEnabled(True)

    def toggle_cheat_map(self):
        do_cheat = self.cheat_map.isChecked()
        for r in range(0, 100):
            for c in range(0, 100):
                cell = self.data[r][c]
                cell.cheat = do_cheat
        self.map_scene.update()
                                            
    def gen_map(self, start_over=True):
        self.alive = True
        self.current_location = [50,50]
        if start_over:
            self.spent_lives = 0
            self.deaths = 0
            self.kills = 0
        self.data = []
        self.rooms = {}
        self.cells_known = []
        self.rooms_known = {}
        self.halls_known = {str([50, 50]): 'known'}
        for item in self.map_scene.items():
            self.map_scene.removeItem(item)
        if self.map_builder.isRunning():
            self.map_builder.stop()
        if self.myself:
            self.map_scene.removeItem(self.myself)
        self.map_builder.continue_chance = 12
        self.map_builder.straight_hall_chance = 16
        self.map_builder.continue_pool = 20
        self.map_builder.generate()
        self.map_builder.start()

    def start_monsters(self):
        if self.monster_timer.isRunning():         
            self.monster_timer.stop()
        for m in self.monsters:
            self.map_scene.removeItem(m)
        self.monsters = []
        self.monster_timer.beasts = []
        for m in range(0, 10):
            monster = Monster(self.data)
            self.monsters.append(monster)
            self.map_scene.addItem(monster)
        if not self.monster_timer.isRunning():            
            self.monster_timer.start()
            
    def fire(self):
        current_row, current_column = self.current_location
        current_cell = self.data[current_row][current_column]
        bullet = Projectile(self.current_location, current_cell.color, self.current_direction)
        self.projectiles.append(bullet)
        self.map_scene.addItem(bullet)
        if not self.bullet_timer.isRunning():
            self.bullet_timer.start()

    def make_triangle(self, direction):
        polygon = QPolygonF()
        if direction == 'south':
            polygon.append(QPointF(5, 8))
            polygon.append(QPointF(2, 2))
            polygon.append(QPointF(8, 2))
            polygon.append(QPointF(5, 8))
        elif direction == 'west':
            polygon.append(QPointF(2, 5))
            polygon.append(QPointF(8, 2))
            polygon.append(QPointF(8, 8))
            polygon.append(QPointF(2, 5))
        elif direction == 'east':
            polygon.append(QPointF(8, 5))
            polygon.append(QPointF(2, 8))
            polygon.append(QPointF(2, 2))
            polygon.append(QPointF(8, 5))
        else:
            polygon.append(QPointF(5, 2))
            polygon.append(QPointF(8, 8))
            polygon.append(QPointF(2, 8))
            polygon.append(QPointF(5, 2))
        return polygon

    def redraw_self(self):
        if self.myself:
            self.map_scene.removeItem(self.myself)
        self.map_scene.update()
        row, column = self.current_location
        self.myself = QGraphicsPolygonItem(self.make_triangle(self.current_direction))
        self.myself.setBrush(QColor(0, 255, 255))
        self.myself.setFillRule(Qt.WindingFill)
        self.map_scene.addItem(self.myself)
        self.myself.setX(column*10+10)
        self.myself.setY(row*10+10)
        self.map_view.centerOn(self.myself)

        if self.projectiles:
            for p in self.projectiles:
                p.update()
                for m in self.monsters:
                    if m.alive:
                        if m.location == p.location:
                            print("YOU KILLED A MONSTER!")
                            m.alive = False
                            p.active = False
                            self.kills += 1
                            self.set_known()
                            p.update()
                
        if self.monsters:
            for m in self.monsters:
                m.visible = False
                m.update()
                row, column = m.location
                if m.location == self.current_location:
                    if m.alive:
                        if self.alive:
                            print("YOU DIED!")
                            self.alive = False
                            self.deaths += 1
                            self.set_known()
                    elif not m.looted:
                        m.looted = True
                        for cell in m.known:
                            if cell not in self.cells_known:
                                row, column = cell
                                self.color_cell(row, column, ghost=True)
                            
                if self.cheat_monsters.isChecked() or [row, column] in self.current_visible:
                    m.visible = True
                    m.update()

        
    def check_for_secrets(self):
        cur_row, cur_col = self.current_location
        item = self.data[cur_row][cur_col]
        for d in ['north', 'south', 'east', 'west']:
            value = getattr(item, d)
            if value and value == 'secret':
                self.door(cur_row, cur_col, d, secret=True)
        color = item.color
        for direction in ['north', 'south', 'west', 'east', 'northwest', 'northeast', 'southwest', 'southeast']:
            next_row = cur_row
            next_col = cur_col
            if 'north' in direction:
                next_row -= 1
            if 'south' in direction:
                next_row += 1
            if 'west' in direction:
                next_col -= 1
            if 'east' in direction:
                next_col += 1
            if next_row <= 0 or next_row >= 99 or next_col <= 0 or next_col >= 99:
                continue
            next_item = self.data[next_row][next_col]
            if next_item.space_type and next_item.color == color:
                for d in ['north', 'south', 'east', 'west']:
                    value = getattr(next_item, d)
                    if value and value == 'secret':
                        self.door(next_row, next_col, d, secret=True)
        
    def look_around(self):
        row, column = self.current_location
        self.color_cell(row, column, known=True)
        self.current_visible = []
        for direction in ['north', 'south', 'west', 'east', 'northwest', 'northeast', 'southwest', 'southeast']:
            self.look(row, column, direction)
        self.check_for_secrets()

        for r in range(0, 100):
            for c in range(0, 100):
                cell = self.data[r][c]
                cell.visible = False
        self.data[row][column].visible = True
        for cv in self.current_visible:
            row, column = cv
            cell = self.data[row][column]
            cell.visible = True
        
    def look(self, row, column, direction):
        cur_row, cur_col = self.current_location
        item = self.data[row][column]
        color = item.color
        if item.space_type == 'room': 
            room_cells = self.rooms.get(str(color))  
            self.current_visible += room_cells
            if str(color) in self.rooms_known:
                return  
            for rc in room_cells:
                r, c = rc
                self.color_cell(r, c, known=True)
                if [r, c] not in self.cells_known:
                    self.cells_known.append([r, c])
            self.rooms_known[str(color)] = 'known'
            self.set_known()
            return
        # hallway 
        next_row = row
        next_col = column
        if 'north' in direction:
            next_row -= 1
        if 'south' in direction:
            next_row += 1
        if 'west' in direction:
            next_col -= 1
        if 'east' in direction:
            next_col += 1
        if (next_row, next_col) != self.exit_door:
            if next_row < 0 or next_row > 99 or next_col < 0 or next_col > 99:
                return
        next_item = self.data[next_row][next_col]
        if next_item.space_type and (next_item.color == color or next_item.space_type == 'exit'):
            if str(next_item.location) not in self.halls_known:
                self.halls_known[str(next_item.location)] = 'known'
                self.color_cell(next_row, next_col, known=True)
                if [next_row, next_col] not in self.cells_known:
                    self.cells_known.append([next_row, next_col])
            self.current_visible += [[next_row, next_col]]
            self.set_known()
            if direction in ['northwest', 'northeast', 'southwest', 'southeast']:
                for sub_d in ['north', 'south', 'west', 'east']:
                    self.look(next_row, next_col, sub_d)
            #else:
            self.look(next_row, next_col, direction)   
            
    def door(self, row, column, direction, secret=False):
        item = self.data[row][column]
        setattr(item, direction, 'door')
        if secret:
            setattr(item, direction, 'known_secret')
        item.update()
            
    def color_cell(self, row, column, ghost=False, known=False):
        item = self.data[row][column]
        cur_row, cur_col = self.current_location
        current_item = self.data[cur_row][cur_col]
        item.ghost = ghost
        item.known = known
        item.update()
        
        if item.space_type != current_item.space_type or ghost:
            return
        for direction in ['north', 'south', 'east', 'west']:
            value = getattr(item, direction)
            if value:
                if value == 'door':
                    self.door(row, column, direction)
                elif self.show_secrets:
                    self.door(row, column, direction, secret=True)

    def move(self, direction):
        if self.paused:
            return
        self.current_direction = direction
        row, column = self.current_location
        next_row = row
        next_col = column
        if direction == 'north':
            next_row -= 1
        elif direction == 'south':
            next_row += 1
        elif direction == 'west':
            next_col -= 1
        elif direction == 'east':
            next_col += 1
        if (next_row, next_col) == self.exit_door:
            self.exits_found += 1
            self.current_location = [next_row, next_col]
            print("YOU REACH THE NEXT DUNGEON LEVEL!")
            self.bonus_points = self.total_points()
            self.gen_map(start_over=False)
            return()
        elif next_row <= 0 or next_row >= 99 or next_col <= 0 or next_col >= 99:
            #print("There be dragons! Can't go that way!")
            return False
        next_item = self.data[next_row][next_col]
        current_item = self.data[row][column]
        if not next_item.space_type:
            #print("Empty space. Can't go that way.")
            return False
        if not next_item.color == current_item.color:
            if not getattr(current_item, direction):
                #print("Wall. You need a door.")
                return False
        self.current_location = [next_row, next_col]
        #print next_item
        self.look_around()
        self.redraw_self()
        
    def collect_rooms(self):
        self.rooms = {}
        self.halways = {}
        for r in range(0, 100):
            for c in range(0, 100):
                try:
                    cell = self.data[r][c]
                    if cell.space_type == 'room':
                        cells = self.rooms.get(str(cell.color), [])
                        cells.append([r, c])
                        self.rooms[str(cell.color)] = cells
                    elif cell.space_type == 'hall':
                        self.halways[str(cell.location)] = 'hallway'
                    elif cell.space_type == 'exit':
                        self.exit_door = (r, c)
                except:
                    print('cannot find cell @ %d,%d' % (r, c))
                    
    def total_points(self):
        return (len(self.rooms_known)*10) + len(self.halls_known) + \
               (self.kills*100) + (self.exits_found*1000) + self.bonus_points
                    
    def set_known(self):
        self.rooms_discovered.setText("%s/%s" % (len(self.rooms_known), len(self.rooms)))
        self.hallway_discovered.setText("%s/%s" % (len(self.halls_known), len(self.halways)))
        self.total_kills.setText("%s/%s" % (self.kills, len(self.monsters)))
        self.cleared_count.setText(str(self.exits_found))
        point_total = self.total_points()
        self.cur_points.setText(str(point_total))
        self.extra_lives = int(point_total/1000) - self.spent_lives
        self.cur_lives.setText(str(self.extra_lives))
        if self.extra_lives:
            self.go_again.setEnabled(True)
        else:
            self.go_again.setEnabled(False)
        
    def save_map(self, exit_cell):
        print(exit_cell)
        self.collect_rooms()
        self.set_known()
        self.color_cell(50, 50, known=True)
        self.current_location = [50, 50]
        self.paused = False
        self.pause()
        self.look_around()
        self.redraw_self()
        self.start_monsters()
        print('jobs done')
        
    def update_image(self, data):
        self.data = data
        for item in self.map_scene.items():
            self.map_scene.removeItem(item)
        for row in list(range(len(self.data))):
            items = self.data[row]
            for c in list(range(len(items))):
                item = items[c]
                self.map_scene.addItem(item)
        self.map_scene.update()
        #self.map_view.fitInView(self.map_scene.itemsBoundingRect())
        
    def update_projectiles(self):
        if not self.paused:
            for projectile in self.projectiles:
                projectile.move()
                r, c = projectile.location
                if r <= 0 or r >= 99 or c <= 0 or c >= 99:
                    projectile.active = False
                else:
                    cell = self.data[r][c]
                    if cell.color != projectile.tile_color:
                        projectile.active = False
            for p in self.projectiles:
                if not p.active:
                    self.map_scene.removeItem(p)
                    self.projectiles.remove(p)
                else:
                    p.update()
            self.redraw_self()

    def update_monsters(self):
        if not self.paused:
            alive_count = 0
            for beast in self.monsters:
                if beast.alive:
                    beast.move(self.current_location, self.alive)
                    alive_count += 1
        #print monsters[0]
        self.redraw_self()
        
def launch_it():
    app = QApplication([])
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    launch_it()
