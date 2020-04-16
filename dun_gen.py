from PySide.QtCore import *
from PySide.QtGui import *
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
        self.map_w = 1000
        self.map_h = 1000
        self.current_location = [50,50]
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
        
        self.bullet_timer = BulletTimeWorker(self.data, parent=self)
        self.bullet_timer.status.connect(self.update_projectiles)
        self.monster_timer = WanderWorker(self.data, parent=self)
        self.monster_timer.status.connect(self.update_monsters)
        self.map_builder = MapBuilderWorker(parent=self)
        self.map_builder.status.connect(self.update_image)
        self.map_builder.finished.connect(self.save_map)
        self.tabWidget.currentChanged.connect(self.toggle_generate)
        
        self.doit.clicked.connect(self.gen_map)
                
        self.map_image = None
        self.known_image = None
                
        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_N:
                print 'generating new map'
                self.gen_map()
                return True
            if not self.alive:
                return False
            if event.key() == Qt.Key_W:
                #print 'moving north'
                self.move('north')
            if event.key() == Qt.Key_A:
                #print 'moving west'
                self.move('west')
            if event.key() == Qt.Key_S:
                #print 'moving south'
                self.move('south')
            if event.key() == Qt.Key_D:
                #print 'moving east'
                self.move('east')
            if event.key() == Qt.Key_Space:
                #print 'firing %s' % self.current_direction
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
                                            
    def gen_map(self):
        self.map_w = self.map_masked.width()
        self.map_h = self.map_masked.height()
        self.alive = True
        self.current_location = [50,50]
        self.data = []
        self.rooms = {}
        self.kills = 0
        self.cells_known = []
        self.rooms_known = {}
        self.halls_known = {str([50,50]):'known'}
        if self.map_builder.isRunning():
            self.map_builder.stop()
        self.map_builder.continue_chance = 12
        self.map_builder.straight_hall_chance = 16
        self.map_builder.continue_pool = 20
        self.map_builder.generate()
        self.known_image = self.map_builder.source_img.copy()
        self.draw = ImageDraw.Draw(self.known_image)
        self.map_builder.start()
        
    def toggle_generate(self):
        if self.tabWidget.currentIndex() == 1:
            self.map_w = self.map_masked.width()
            self.map_h = self.map_masked.height()
            self.doit.setEnabled(False)
        else:
            self.doit.setEnabled(True)
            
    def start_monsters(self):
        if self.monster_timer.isRunning():         
            self.monster_timer.stop() 
        self.monster_timer.beasts = []
        for m in range(0,10):
            self.monster_timer.add()
        if not self.monster_timer.isRunning():            
            self.monster_timer.start()
            
    def fire(self):
        current_row, current_column = self.current_location
        current_cell = self.data[current_row][current_column]
        self.bullet_timer.add(self.current_location, current_cell.color, self.current_direction)
        if not self.bullet_timer.isRunning():            
            self.bullet_timer.start()
                
    def redraw_self(self):
        temp_image = self.known_image.copy()
        #cheater mode
        #temp_image = self.map_image.copy()
        draw = ImageDraw.Draw(temp_image)
        row, column = self.current_location
        if not self.alive:
            draw.ellipse([(column*10)+2, (row*10)+2, (column*10)+8, (row*10)+8], outline='red', fill='red')
        if self.current_direction == 'east':
            draw.polygon([((column*10)+2, (row*10)+2), ((column*10)+2, (row*10)+8), ((column*10)+8, (row*10)+5)], outline='black', fill=(5, 173, 235))
        elif self.current_direction == 'west':
            draw.polygon([((column*10)+8, (row*10)+2), ((column*10)+8, (row*10)+8), ((column*10)+2, (row*10)+5)], outline='black', fill=(5, 173, 235))
        elif self.current_direction == 'north':
            draw.polygon([((column*10)+5, (row*10)+2), ((column*10)+2, (row*10)+8), ((column*10)+8, (row*10)+8)], outline='black', fill=(5, 173, 235))
        elif self.current_direction == 'south':
            draw.polygon([((column*10)+5, (row*10)+8), ((column*10)+2, (row*10)+2), ((column*10)+8, (row*10)+2)], outline='black', fill=(5, 173, 235))
        else:
            draw.ellipse([(column*10)+2, (row*10)+2, (column*10)+8, (row*10)+8], outline='black', fill=(5, 173, 235))
            
        if self.projectiles:
            for p in self.projectiles:
                if not p.active:
                    return
                row, column = p.location
                draw.ellipse([(column*10)+2, (row*10)+2, (column*10)+8, (row*10)+8], outline='yellow', fill='red')
                for m in self.monsters:
                    if m.alive:
                        if m.location == p.location:
                            print "YOU KILLED A MONSTER!"
                            m.alive = False
                            p.active = False
                            self.kills+=1
                            self.set_known()
                
        if self.monsters:
            debug = False
            for m in self.monsters:
                #pathing debug
                #for p in m.current_path:
                #    r, c = p
                #    draw.ellipse([(c*10)+2, (r*10)+2, (c*10)+8, (r*10)+8], outline='green', fill='blue')
                row, column = m.location
                if m.location == self.current_location:
                    if m.alive:
                        print "YOU DIED!"
                        self.alive = False
                    elif not m.looted:
                        m.looted = True
                        for cell in m.known:
                            if cell not in self.cells_known:
                                row, column = cell
                                self.color_cell(row, column, ghost=True)
                            
                if debug or [row,column] in self.current_visible:
                    if m.alive:
                        draw.ellipse([(column*10)+2, (row*10)+2, (column*10)+8, (row*10)+8], outline='green', fill='red')
                    else:
                        draw.ellipse([(column*10)+2, (row*10)+2, (column*10)+8, (row*10)+8], outline='red', fill='black')

        for cv in self.current_visible:
            row, column = cv
            irow = row*10
            icol = column*10
            draw.rectangle((icol, irow, icol+10, irow+10), fill=None, outline='yellow')

        row, column = self.current_location
        cropped = temp_image.crop([(column*10)-250, (row*10)-250, (column*10)+250, (row*10)+250])
        #resized = cropped.resize((self.map_w,self.map_h))
        bytes = cropped.tobytes("raw","RGB")
        qim = QImage(bytes, cropped.size[0], cropped.size[1], QImage.Format_RGB888)
        self.map_masked.setPixmap(QPixmap(qim).scaled(QSize(self.map_w,self.map_h)))
        
    def check_for_secrets(self):
        is_near = False
        cur_row, cur_col = self.current_location
        item = self.data[cur_row][cur_col]
        color = item.color
        for direction in ['north','south','west','east','northwest','northeast','southwest','southeast']:
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
            if next_row<=0 or next_row>=99 or next_col<=0 or next_col>=99:
                continue
            next_item = self.data[next_row][next_col]
            if next_item.space_type and next_item.color == color:
                for d in ['north', 'south', 'east', 'west']:
                    value = getattr(next_item, d)
                    if value and value == 'secret':
                        self.door(next_row, next_col, d, secret=True)
        
    def look_around(self):
        row, column = self.current_location
        item = self.data[row][column]
        #print item
        self.color_cell(row, column)
        self.current_visible = []
        for direction in ['north','south','west','east','northwest','northeast','southwest','southeast']:
            self.look(row, column, direction)
        self.check_for_secrets()
        
    def look(self, row, column, direction):
        cur_row, cur_col = self.current_location
        item = self.data[row][column]
        color = item.color
        if item.space_type == 'room': 
            room_cells = self.rooms.get(str(color))  
            self.current_visible += room_cells
            self.border_room(room_cells)
            if str(color) in self.rooms_known:
                return  
            for rc in room_cells:
                r,c = rc
                self.color_cell(r,c)    
                if [r,c] not in self.cells_known:
                    self.cells_known.append([r,c])
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
            if next_row<=0 or next_row>=99 or next_col<=0 or next_col>=99:
                return
        next_item = self.data[next_row][next_col]
        if next_item.space_type and (next_item.color == color or next_item.space_type == 'exit'):
            if str(next_item.location) not in self.halls_known:
                self.halls_known[str(next_item.location)] = 'known'
                self.color_cell(next_row,next_col)
                if [next_row,next_col] not in self.cells_known:
                    self.cells_known.append([next_row,next_col])
            self.current_visible += [[next_row,next_col]]
            self.set_known()
            if direction in ['northwest','northeast','southwest','southeast']:
                for sub_d in ['north','south','west','east']:
                    self.look(next_row, next_col, sub_d)
            #else:
            self.look(next_row, next_col, direction)   
            
    def door(self, row, column, direction, secret=False):
        irow = row*10
        icol = column*10
        outline = (0,0,255)
        if secret:
            outline = (150,0,150)
        if direction == 'east':
            self.draw.rectangle((icol+7, irow+2, icol+9, irow+8), fill=(0,0,0), outline=outline)
        if direction == 'west':
            self.draw.rectangle((icol+1, irow+2, icol+3, irow+8), fill=(0,0,0), outline=outline)
        if direction == 'north':
            self.draw.rectangle((icol+2, irow+1, icol+8, irow+3), fill=(0,0,0), outline=outline)
        if direction == 'south':
            self.draw.rectangle((icol+2, irow+7, icol+8, irow+9), fill=(0,0,0), outline=outline)
            
    def color_cell(self, row, column, outline='grey', ghost=False):
        item = self.data[row][column]
        cur_row,cur_col = self.current_location
        current_item = self.data[cur_row][cur_col]
        color = item.color
        irow = row*10
        icol = column*10
        if item.space_type == 'room':
            color = (160,160,160)
        if item.space_type == 'exit':
            self.draw.rectangle((icol, irow, icol+10, irow+10), fill=(0,0,0), outline='yellow')
            self.draw.rectangle((icol+2, irow+2, icol+8, irow+8), fill=(255,0,0), outline='green')
            self.draw.rectangle((icol+4, irow+4, icol+6, irow+6), fill=(255,255,0), outline='blue')
        elif ghost:
            self.draw.rectangle((icol, irow, icol+10, irow+10), fill=(20,20,20), outline=(30,30,30))
        else:
            self.draw.rectangle((icol, irow, icol+10, irow+10), fill=color, outline=outline)
        
        if item.space_type != current_item.space_type or ghost:
            return
        for direction in ['north', 'south', 'east', 'west']:
            value = getattr(item, direction)
            if value:
                if value == 'door':
                    self.door(row, column, direction)
                elif self.show_secrets:
                    self.door(row, column, direction, secret=True)
            
    def border_room(self, room, outline='white'):
        r,c = room[0]
        start = self.data[r][c]
        my_color = start.color
        for cell in room:
            r,c = cell
            irow = r*10
            icol = c*10
            # is north wall?
            if r==0:
                self.draw.line((icol, irow, icol+10, irow), fill='black', width=3)
                self.draw.line((icol, irow, icol+10, irow), fill=outline, width=1)
            else:        
                north = self.data[r-1][c]
                if north.color != my_color:
                    self.draw.line((icol, irow, icol+10, irow), fill='black', width=3)
                    self.draw.line((icol, irow, icol+10, irow), fill=outline, width=1)
            # is south wall?
            if r==99:
                self.draw.line((icol, irow+10, icol+10, irow+10), fill='black', width=3)
                self.draw.line((icol, irow+10, icol+10, irow+10), fill=outline, width=1)
            else:        
                south = self.data[r+1][c]
                if south.color != my_color:
                    self.draw.line((icol, irow+10, icol+10, irow+10), fill='black', width=3)
                    self.draw.line((icol, irow+10, icol+10, irow+10), fill=outline, width=1)
            # is west wall?
            if c==0:
                self.draw.line((icol, irow, icol, irow+10), fill='black', width=3)
                self.draw.line((icol, irow, icol, irow+10), fill=outline, width=1)
            else:        
                west = self.data[r][c-1]
                if west.color != my_color:
                    self.draw.line((icol, irow, icol, irow+10), fill='black', width=3)
                    self.draw.line((icol, irow, icol, irow+10), fill=outline, width=1)
            # is east wall?
            if c==99:
                self.draw.line((icol+10, irow, icol+10, irow+10), fill='black', width=3)
                self.draw.line((icol+10, irow, icol+10, irow+10), fill=outline, width=1)
            else:        
                east = self.data[r][c+1]
                if east.color != my_color:
                    self.draw.line((icol+10, irow, icol+10, irow+10), fill='black', width=3)
                    self.draw.line((icol+10, irow, icol+10, irow+10), fill=outline, width=1)
        
    def move(self, direction):
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
        if (next_row,next_col) == self.exit_door:
            print "YOU EXIT THE DUNGEON!"
        elif next_row<=0 or next_row>=99 or next_col<=0 or next_col>=99:
            print "There be dragons! Can't go that way!"
            return False
        next_item = self.data[next_row][next_col]
        current_item = self.data[row][column]
        if not next_item.space_type:
            print "Empty space. Can't go that way."
            return False
        if not next_item.color == current_item.color:
            if not getattr(current_item, direction):
                print "Wall. You need a door."
                return False
        self.current_location = [next_row, next_col]
        #print next_item
        self.look_around()
        self.redraw_self()
        
    def collect_rooms(self):
        self.rooms = {}
        self.halways = {}
        for r in range(0,100):
            for c in range(0, 100):
                cell = self.data[r][c]
                if cell.space_type == 'room':
                    cells = self.rooms.get(str(cell.color), [])
                    cells.append([r,c])
                    self.rooms[str(cell.color)] = cells
                elif cell.space_type == 'hall':
                    self.halways[str(cell.location)] = 'hallway'
                elif cell.space_type == 'exit':
                    self.exit_door = (r,c)
                    
    def set_known(self):
        self.rooms_discovered.setText("%s/%s" % (len(self.rooms_known), len(self.rooms)))
        self.hallway_discovered.setText("%s/%s" % (len(self.halls_known), len(self.halways)))
        self.total_kills.setText("%s/%s" % (self.kills, len(self.monsters)))
        
    def save_map(self, image):
        image.save(r'D:\Dev\Python\dun_gen\test.bmp')
        self.update_image(image)
        self.data = self.map_builder.data
        self.collect_rooms()
        self.set_known()
        self.color_cell(50,50)
        self.look_around()
        self.redraw_self()
        self.bullet_timer.data = self.data
        self.monster_timer.data = self.data
        self.start_monsters()
        print 'jobs done'
        
    def update_image(self, image):
        self.map_image = image
        data = image.tobytes("raw","RGB")
        qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
        self.map.setPixmap(QPixmap(qim))
        
    def update_projectiles(self, projectiles):
        self.projectiles = projectiles
        self.redraw_self()
        
    def update_monsters(self, monsters):
        self.monsters = monsters
        #print monsters[0]
        self.redraw_self()
        
def launch_it():
    app = QApplication([])
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    launch_it()
