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

class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        
        loadUi(r"%s\dun_gen.ui" % here, self)
        self.current_location = [99,50]
        self.data = []
        self.shown = []
        self.rooms = {}
        
        self.map_builder = MapBuilderWorker(parent=self)
        self.map_builder.status.connect(self.update_image)
        self.map_builder.finished.connect(self.save_map)
        
        self.doit.clicked.connect(self.gen_map)
        self.north_entrance.clicked.connect(partial(self.add_to_map, "north"))
        self.east_entrance.clicked.connect(partial(self.add_to_map, "east"))
        self.west_entrance.clicked.connect(partial(self.add_to_map, "west"))
        
        self.move_north.clicked.connect(partial(self.move, 'north'))
        self.move_south.clicked.connect(partial(self.move, 'south'))
        self.move_west.clicked.connect(partial(self.move, 'west'))
        self.move_east.clicked.connect(partial(self.move, 'east'))
        
        self.also_straight.valueChanged.connect(self.update_also_straight)
        self.no_change.valueChanged.connect(self.update_no_change)
        sel_model = self.operations.selectionModel()
        sel_model.selectionChanged.connect(self.highlight_selection)
        
        self.update_also_straight()
        self.update_no_change()
        self.splitter.setSizes([1010, 200])
        self.map_image = None
        self.known_image = None
        
    def update_also_straight(self, *args):
        self.also_straight_value.setText(str(self.also_straight.value()))
        
    def update_no_change(self, *args):
        self.no_change_value.setText(str(self.no_change.value()))
        
    def highlight_selection(self, selection):
        sel_row = selection.indexes()[0].row()
        contents = self.operations.item(sel_row).text()
        test = re.search('\[(.*),(.*)\].*', contents)
        if test:
            temp_image = self.map_image.copy()
            draw = ImageDraw.Draw(temp_image)
            font = ImageFont.truetype("arial.ttf", 20)
            draw.text((int(test.groups()[1])*10-2, int(test.groups()[0])*10-2), 'O', font=font, fill='black')
            font = ImageFont.truetype("arial.ttf", 18)
            draw.text((int(test.groups()[1])*10, int(test.groups()[0])*10), 'X', font=font, fill='red')
            data = temp_image.tobytes("raw","RGB")
            qim = QImage(data, temp_image.size[0], temp_image.size[1], QImage.Format_RGB888)
            self.map.setPixmap(QPixmap(qim))
        
    def gen_map(self):
        self.current_location = [99,50]
        self.data = []
        self.shown = []
        self.rooms = {}
        if self.map_builder.isRunning():
            self.map_builder.stop()
        self.map_builder.continue_chance = self.also_straight.value()
        self.map_builder.straight_hall_chance = self.no_change.value()
        self.map_builder.continue_pool = self.also_straight.maximum()
        self.map_builder.start_entrance = 'south'
        self.map_builder.generate()
        self.known_image = self.map_builder.source_img.copy()
        self.draw = ImageDraw.Draw(self.known_image)
        self.operations.clear()
        self.map_builder.start()
        
    def add_to_map(self, direction):
        print 'adding %s entrance' % direction
        if self.map_builder.isRunning():
            self.map_builder.stop()
        self.map_builder.continue_chance = self.also_straight.value()
        self.map_builder.straight_hall_chance = self.no_change.value()
        self.map_builder.continue_pool = self.also_straight.maximum()
        self.map_builder.start_entrance = direction
        self.map_builder.start()
        
    def redraw_self(self):
        temp_image = self.known_image.copy()
        draw = ImageDraw.Draw(temp_image)
        row, column = self.current_location
        font = ImageFont.truetype("arial.ttf", 16)
        draw.text(((column*10)-2, (row*10)-2), 'O', font=font, fill='black')
        font = ImageFont.truetype("arial.ttf", 14)
        draw.text(((column*10), (row*10-2)), 'X', font=font, fill='red')
        data = temp_image.tobytes("raw","RGB")
        qim = QImage(data, temp_image.size[0], temp_image.size[1], QImage.Format_RGB888)
        self.map_masked.setPixmap(QPixmap(qim))
        
    def look_around(self):
        row, column = self.current_location
        item = self.data[row][column]
        print item
        self.shown.append([row, column])
        self.color_cell(row, column)
        for direction in ['north','south','west','east','northwest','northeast','southwest','southeast']:
            self.look(row, column, direction)
        
    def look(self, row, column, direction):
        item = self.data[row][column]
        color = item.color
        if item.space_type == 'room':
            room_cells = self.rooms.get(str(color), [])
            for rc in room_cells:
                r,c = rc
                self.shown.append([r,c])
                self.color_cell(r,c)
            self.border_room(room_cells)
            for rc in room_cells:
                r,c = rc
                item = self.data[r][c]
                for door in item.doors:
                    self.door(r, c, door)
                for sd in item.secrets:
                    self.door(r, c, sd, secret=True)
            return
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
        if next_row<=0 or next_row>=99 or next_col<=0 or next_col>=99:
            return
        next_item = self.data[next_row][next_col]
        if next_item.space_type and next_item.color == color:
            self.shown.append([next_row,next_col])
            self.color_cell(next_row,next_col)
            self.look(next_row, next_col, direction)   
            
    def door(self, row, column, direction, secret=False):
        irow = row*10
        icol = column*10
        outline = (0,0,255)
        if secret:
            outline = 'red'
        if direction == 'east':
            self.draw.rectangle((icol+8, irow+2, icol+12, irow+8), fill=(0,0,0), outline=outline)
        if direction == 'west':
            self.draw.rectangle((icol-2, irow+2, icol+2, irow+8), fill=(0,0,0), outline=outline)
        if direction == 'north':
            self.draw.rectangle((icol+2, irow-2, icol+8, irow+2), fill=(0,0,0), outline=outline)
        if direction == 'south':
            self.draw.rectangle((icol+2, irow+8, icol+8, irow+12), fill=(0,0,0), outline=outline)
            
    def color_cell(self, row, column, outline='grey'):
        item = self.data[row][column]
        color = item.color
        irow = row*10
        icol = column*10
        self.draw.rectangle((icol, irow, icol+10, irow+10), fill=color, outline=outline)
        if item.space_type == 'hall':
            for door in item.doors:
                self.door(row, column, door)
            for sd in item.secrets:
                self.door(row, column, sd, secret=True)
            
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
        if next_row<=0 or next_row>=99 or next_col<=0 or next_col>=99:
            print "There be dragons! Can't go that way!"
            return False
        next_item = self.data[next_row][next_col]
        current_item = self.data[row][column]
        if not next_item.space_type:
            print "Empty space. Can't go that way."
            return False
        if not next_item.color == current_item.color:
            if direction not in current_item.doors and direction not in current_item.secrets:
                print "Wall. You need a door."
                return False
        self.current_location = [next_row, next_col]
        #if [next_row, next_col] not in self.shown:
        self.look_around()
        self.redraw_self()
        
    def collect_rooms(self):
        self.rooms = {}
        for r in range(0,100):
            for c in range(0, 100):
                cell = self.data[r][c]
                if cell.space_type == 'room':
                    cells = self.rooms.get(str(cell.color), [])
                    cells.append([r,c])
                    self.rooms[str(cell.color)] = cells
        
    def save_map(self, image):
        image.save(r'D:\Dev\Python\dun_gen\test.bmp')
        self.data = self.map_builder.data
        self.collect_rooms()
        print 'done'
        
    def update_image(self, image):
        self.map_image = image
        data = image.tobytes("raw","RGB")
        qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
        self.map.setPixmap(QPixmap(qim))
        
def launch_it():
    app = QApplication([])
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    launch_it()
