from PySide.QtCore import *
from PySide.QtGui import *
from customLoader import loadUi
import os
import time
import math
import sys
import random
from PIL import Image, ImageDraw

here = os.path.dirname(__file__)

class Cell(object):
    north = False
    east = False
    west = False
    south = False
    space_type = None
    name = None
    color = (125,125,125)
    location = [None,None]

    def __init__(self, location):
        self.location = location

class MapBuilderWorker(QThread):
    status = Signal(object)
    finished = Signal(object)
    data = []
    source_img = None
    draw = None
    delay = .01

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def generate(self):
        self.data = []
        self.source_img = Image.new('RGB', (1000,1000))
        self.draw = ImageDraw.Draw(self.source_img)
        for r in range(0,100):
            row = []
            for c in range(0, 100):
                cell = Cell([r,c])
                row.append(cell)
            self.data.append(row)
            
    def max_box(self, direction, current_location, color):
        largest_desired_room = 12
        row, column = current_location
        max_space = 1
        print 'checking area %s of %s' % (direction, current_location)
        while max_space <= largest_desired_room:
            for r in range(0, max_space):
                for c in range(0, max_space):
                    if [r,c] != [0,0]:
                        if direction == "northwest":
                            r_test = row - r
                            c_test = column - c
                        elif direction == "northeast":
                            r_test = row - r
                            c_test = column + c
                        elif direction == "southwest":
                            r_test = row + r
                            c_test = column - c
                        elif direction == "southeast":
                            r_test = row + r
                            c_test = column + c
                        if r_test<0 or r_test>=99 or c_test<0 or c_test>=99:
                            print "box test out of bounds [%s,%s]" % (r_test, c_test)
                            return max_space - 1
                        nw = self.data[r_test][c_test]
                        if nw.space_type is not None:
                            if nw.color != color:
                                return max_space -1
            max_space += 1
        return largest_desired_room
            
    def run(self):
        self.generate()
        self.add_random_item(98, 50, 'north', space_type='hall')
        self.finished.emit(self.source_img)
        
    def color_cell(self, row, column, color, space_type, outline=None):
        nw = self.data[row][column]
        nw.space_type = space_type
        nw.color = color
        irow = row*10
        icol = column*10
        self.draw.rectangle((icol, irow, icol+10, irow+10), fill=color, outline=outline)
        self.status.emit(self.source_img)
        time.sleep(self.delay)
        
    def add_random_item(self, row, column, direction, space_type=None, outline=None):
        if row<0 or row>=99 or column<0 or column>=99:
            return
        cur_item = self.data[row][column]
        if cur_item.space_type:
            return
        if space_type:
            this_type = space_type
        else:
            roll = random.randint(1,6)
            if roll <= 3:
                this_type = 'hall'
            else:
                this_type = 'room'
        print 'adding %s %s from (%s,%s)' % (this_type, direction, row, column)
        next_row = row
        next_col = column
        red = random.randint(20,256)
        blue = random.randint(20,256)
        green = random.randint(20,256)
        color = (red,green,blue)
        #self.data[row][column] =  cur_item
        if this_type == 'room':
            cur_item.space_type = this_type
            roll = random.randint(1,3)
            if direction == 'north':
                if roll in [1,2]:
                    #handle northwest
                    max_dist = self.max_box('northwest',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for r in range(row, row-distance, -1):
                            for c in range(column, column-distance, -1):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            #west wall
                            where = random.randint(row-distance+2, row-2)
                            self.add_random_item(where, column-distance, 'west', space_type='hall', outline='white')
                        if wall in [1,3]:
                            #north wall
                            where = random.randint(column-distance+2, column-2)
                            self.add_random_item(row-distance, column, 'north', space_type='hall', outline='white')
                if roll in [1,3]:
                    #handle northeast
                    max_dist = self.max_box('northeast',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for r in range(row, row-distance, -1):
                            for c in range(column, column+distance):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            #east wall
                            where = random.randint(row-distance+2, row-2)
                            self.add_random_item(where, column-distance, 'west', space_type='hall', outline='white')
                        if wall in [1,3]:
                            #north wall
                            where = random.randint(column+2, column+distance-2)
                            self.add_random_item(row-distance, column, 'north', space_type='hall', outline='white')
            if direction == 'south':
                if roll in [1,2]:
                    #handle southwest
                    max_dist = self.max_box('southwest',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for r in range(row, row+distance):
                            for c in range(column, column-distance, -1):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            self.add_random_item(row, column-distance, 'west', space_type='hall')
                        if wall in [1,3]:
                            self.add_random_item(row+distance, column, 'south', space_type='hall')
                if roll in [1,3]:
                    #handle southeast
                    max_dist = self.max_box('southeast',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for r in range(row, row+distance):
                            for c in range(column, column+distance):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            self.add_random_item(row, column+distance, 'east', space_type='hall')
                        if wall in [1,3]:
                            self.add_random_item(row+distance, column, 'south', space_type='hall')
            if direction == 'east':
                if roll in [1,2]:
                    #handle northeast
                    max_dist = self.max_box('northeast',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for c in range(column, column+distance):
                            for r in range(row, row-distance, -1):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            self.add_random_item(row, column+distance, 'east', space_type='hall')
                        if wall in [1,3]:
                            self.add_random_item(row-distance, column, 'north', space_type='hall')
                if roll in [1,3]:
                    #handle southeast
                    max_dist = self.max_box('southeast',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for c in range(column, column+distance):
                            for r in range(row, row+distance):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            self.add_random_item(row, column+distance, 'east', space_type='hall')
                        if wall in [1,3]:
                            self.add_random_item(row+distance, column, 'south', space_type='hall')
            if direction == 'west':
                if roll in [1,2]:
                    #handle northwest
                    max_dist = self.max_box('northwest',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for c in range(column, column-distance,-1):
                            for r in range(row, row-distance, -1):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            self.add_random_item(row, column-distance, 'west', space_type='hall')
                        if wall in [1,3]:
                            self.add_random_item(row-distance, column, 'north', space_type='hall')
                if roll in [1,3]:
                    #handle southwest
                    max_dist = self.max_box('southwest',cur_item.location, color)
                    print 'max wall length: %s' % max_dist
                    if max_dist == 2:
                        distance = 2
                    elif max_dist > 2:
                        distance = random.randint(2,max_dist)
                    else:
                        distance = 0
                    if max_dist >= 2:
                        for c in range(column, column-distance,-1):
                            for r in range(row, row+distance):
                                self.color_cell(r, c, color, this_type)
                    if distance < max_dist and distance > 4:
                        wall = random.randint(1,6)
                        if wall in [1,2]:
                            self.add_random_item(row, column-distance, 'west', space_type='hall')
                        if wall in [1,3]:
                            self.add_random_item(row+distance, column, 'south', space_type='hall')
            self.color_cell(row, column, color, this_type, outline='red')
        else:
            max_len = 1
            hall_len = random.randint(4,20)
            connection = False
            out_of_bounds = False
            to_make_hall = []
            for each in range(1,hall_len):
                max_len += 1
                if direction == 'north':
                    next_row -= 1
                elif direction == 'south':
                    next_row += 1
                elif direction == 'west':
                    next_col -= 1
                elif direction == 'east':
                    next_col += 1
                if next_row<0 or next_row>=99 or next_col<0 or next_col>=99:
                    max_len -= 1
                    out_of_bounds = True
                    break
                next_item = self.data[next_row][next_col]
                if next_item.space_type: 
                    #next_item.color = (255,255,255)
                    connection = next_item
                    break
                else:
                    to_make_hall.append(next_item)
                    
            #if out_of_bounds or max_len < 3:
                #return
                
            cur_item.space_type = this_type
            #cur_item.color = (red,green,blue)
            cur_item.color = 'grey'
            irow = row*10
            icol = column*10
            self.draw.rectangle((icol, irow, icol+10, irow+10), fill='grey', outline=outline)
            self.status.emit(self.source_img)
            time.sleep(self.delay)
            for item in to_make_hall:
                item.space_type = 'hall'
                #item.color = (red,green,blue)
                item.color = 'grey'
                r,c = item.location
                irow = r*10
                icol = c*10
                self.draw.rectangle((icol, irow, icol+10, irow+10), fill='grey', outline=None)
                self.status.emit(self.source_img)
                time.sleep(self.delay)
            #if connection:
                #connection.color = (255,255,255)
                    
            if direction == 'north':
                next_row -= 1
            elif direction == 'south':
                next_row += 1
            elif direction == 'west':
                next_col -= 1
            elif direction == 'east':
                next_col += 1
            if next_row>0 and next_row<=99 and next_col>0 and next_col<=99:
                next_item = self.data[next_row][next_col]
                if next_item.space_type: 
                    #next_item.color = (255,255,255)
                    connection = next_item
                    
            just_branched = False
            if max_len < 4:
                just_branched = True
            for each in range(3,max_len):
                if just_branched:
                    roll = 0
                else:
                    roll = random.randint(1,20)
                if connection:
                    if each+3 >= max_len:
                        print 'connected'
                        break
                elif each+1 == max_len:
                    print 'corner'
                    roll = random.randint(17,20)
                    
                if direction == 'north':
                    next_row = row - each
                if direction == 'south':
                    next_row = row + each
                if direction == 'west':
                    next_col = column - each
                if direction == 'east':
                    next_col = column + each
                    
                if direction in ['north', 'south']:
                    if next_col+1>99 and roll in [17,18,19]:
                        roll = 20
                    if next_col-1<0 and roll in [17,18,20]:
                        roll = 19
                    if roll in [17,18,19]:
                        just_branched = True
                        self.add_random_item(next_row, next_col+1, 'east')
                    if roll in [17,18,20]:
                        just_branched = True
                        self.add_random_item(next_row, next_col-1, 'west')
                        
                if direction in ['east', 'west']:
                    if next_row+1>99 and roll in [17,18,19]:
                        roll = 20
                    if next_row-1<0 and roll in [17,18,20]:
                        roll = 19
                    if roll in [17,18,19]:
                        just_branched = True
                        self.add_random_item(next_row+1, next_col, 'south')
                    if roll in [17,18,20]:
                        just_branched = True
                        self.add_random_item(next_row-1, next_col, 'north')
        
    def stop(self):
        self.terminate()
        
class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        
        loadUi(r"%s\dun_gen.ui" % here, self)
        
        self.map_builder = MapBuilderWorker(parent=self)
        self.map_builder.status.connect(self.update_image)
        self.map_builder.finished.connect(self.save_map)
        self.doit.clicked.connect(self.gen_map)
        
    def gen_map(self):
        if self.map_builder.isRunning():
            self.map_builder.stop()
        self.map_builder.start()
        
    def save_map(self, image):
        image.save(r'D:\Dev\Python\dun_gen\test.bmp')
        print 'done'
        
    def update_image(self, image):
        height = self.map.width()
        data = image.tobytes("raw","RGB")
        qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
        pixmap = QPixmap(qim).scaled(height, height, Qt.KeepAspectRatio)
        self.map.setPixmap(pixmap)
        
def launch_it():
    app = QApplication([])
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    launch_it()

class Table(object):
    data = []
    
    def __init__(self):
        self.generate()
        self.randomize()
        self.draw()
        
    def generate(self):
        for r in range(0,100):
            row = []
            for c in range(0, 100):
                cell = Cell([r,c])
                row.append(cell)
            self.data.append(row)
            
    def randomize(self):
        self.add_random_item(98, 50, 'north', space_type='hall')
        
    def add_random_item(self, row, column, direction, space_type=None):
        if row<0 or row>=99 or column<0 or column>=99:
            return
        cur_item = self.data[row][column]
        if cur_item.space_type:
            return
        print 'headed %s (%s,%s)' % (direction, row, column)
        if space_type:
            this_type = space_type
        else:
            roll = random.randint(1,6)
            if roll <= 3:
                this_type = 'hall'
            else:
                this_type = 'room'
        next_row = row
        next_col = column
        red = random.randint(20,256)
        blue = random.randint(20,256)
        green = random.randint(20,256)
        #self.data[row][column] =  cur_item
        if this_type == 'room':
            cur_item.space_type = this_type
            cur_item.color = (red,green,blue)
            max_horiz = 0
            max_vert = 0
            #get max room size
            room_items = [cur_item.location]
            roll = random.randint(1,3)
            if direction == 'north':
                if roll in [1,2]:
                    #handle northwest
                    distance = random.randint(2,8)
                    for r in range(row, row-distance, -1):
                        for c in range(column, column-distance, -1):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
                if roll in [1,3]:
                    #handle northeast
                    distance = random.randint(2,8)
                    for r in range(row, row-distance, -1):
                        for c in range(column, column+distance):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
            if direction == 'south':
                if roll in [1,2]:
                    #handle southwest
                    distance = random.randint(2,8)
                    for r in range(row, row+distance):
                        for c in range(column, column-distance, -1):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
                if roll in [1,3]:
                    #handle southeast
                    distance = random.randint(2,8)
                    for r in range(row, row+distance):
                        for c in range(column, column+distance):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
            if direction == 'east':
                if roll in [1,2]:
                    #handle northeast
                    distance = random.randint(2,8)
                    for r in range(row, row-distance, -1):
                        for c in range(column, column+distance):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
                if roll in [1,3]:
                    #handle southeast
                    distance = random.randint(2,8)
                    for r in range(row, row+distance):
                        for c in range(column, column+distance):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
            if direction == 'west':
                if roll in [1,2]:
                    #handle northwest
                    distance = random.randint(2,8)
                    for r in range(row, row-distance, -1):
                        for c in range(column, column-distance,-1):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
                if roll in [1,3]:
                    #handle southwest
                    distance = random.randint(2,8)
                    for r in range(row, row+distance):
                        for c in range(column, column-distance,-1):
                            if r<0 or r>=99 or c<0 or c>=99:
                                break
                            nw = self.data[r][c]
                            if nw.location not in room_items and nw.space_type is not None:
                                nw.space_type = this_type
                                nw.color = (red,green,blue)
        else:
            max_len = 1
            hall_len = random.randint(4,20)
            connection = False
            out_of_bounds = False
            to_make_hall = []
            for each in range(1,hall_len):
                max_len += 1
                if direction == 'north':
                    next_row -= 1
                elif direction == 'south':
                    next_row += 1
                elif direction == 'west':
                    next_col -= 1
                elif direction == 'east':
                    next_col += 1
                if next_row<0 or next_row>=99 or next_col<0 or next_col>=99:
                    max_len -= 1
                    out_of_bounds = True
                    break
                next_item = self.data[next_row][next_col]
                if next_item.space_type: 
                    #next_item.color = (255,255,255)
                    connection = next_item
                    break
                else:
                    to_make_hall.append(next_item)
                    
            #if out_of_bounds or max_len < 3:
                #return
                
            cur_item.space_type = this_type
            #cur_item.color = (red,green,blue)
            cur_item.color = 'grey'
            for item in to_make_hall:
                item.space_type = 'hall'
                #item.color = (red,green,blue)
                item.color = 'grey'
            #if connection:
                #connection.color = (255,255,255)
                    
            if direction == 'north':
                next_row -= 1
            elif direction == 'south':
                next_row += 1
            elif direction == 'west':
                next_col -= 1
            elif direction == 'east':
                next_col += 1
            if next_row>0 and next_row<=99 and next_col>0 and next_col<=99:
                next_item = self.data[next_row][next_col]
                if next_item.space_type: 
                    #next_item.color = (255,255,255)
                    connection = next_item
                    
            just_branched = False
            if max_len < 4:
                just_branched = True
            for each in range(3,max_len):
                if just_branched:
                    roll = 0
                else:
                    roll = random.randint(1,20)
                if connection:
                    if each+3 >= max_len:
                        print 'connected'
                        break
                elif each+1 == max_len:
                    print 'corner'
                    roll = random.randint(16,20)
                    
                if direction == 'north':
                    next_row = row - each
                if direction == 'south':
                    next_row = row + each
                if direction == 'west':
                    next_col = column - each
                if direction == 'east':
                    next_col = column + each
                    
                if direction in ['north', 'south']:
                    if next_col+1>99 and roll in [17,18,19]:
                        roll = 20
                    if next_col-1<0 and roll in [17,18,20]:
                        roll = 19
                    if roll in [17,18,19]:
                        just_branched = True
                        self.add_random_item(next_row, next_col+1, 'east')
                    if roll in [17,18,20]:
                        just_branched = True
                        self.add_random_item(next_row, next_col-1, 'west')
                    if roll in [15, 16]:
                        if direction == 'east':
                            next_col += 1
                        if direction == 'west':
                            next_col -= 1
                        self.add_random_item(next_row, next_col, direction, space_type='room')
                        
                if direction in ['east', 'west']:
                    if next_row+1>99 and roll in [17,18,19]:
                        roll = 20
                    if next_row-1<0 and roll in [17,18,20]:
                        roll = 19
                    if roll in [17,18,19]:
                        just_branched = True
                        self.add_random_item(next_row+1, next_col, 'south')
                    if roll in [17,18,20]:
                        just_branched = True
                        self.add_random_item(next_row-1, next_col, 'north')
                    if roll in [15, 16]:
                        if direction == 'south':
                            next_row += 1
                        if direction == 'north':
                            next_row -= 1
                        self.add_random_item(next_row, next_col, direction, space_type='room')
            
    def draw(self):
        source_img = Image.new('RGB', (1000,1000))
        print 'type =',type(source_img)
        return
        draw = ImageDraw.Draw(source_img)
        for r in range(0, 100):
            for c in range(0, 100):
                item = self.data[r][c]
                row = r*10
                col = c*10
                fill = 'black'
                if item.space_type:
                    fill = item.color
                    #print 'drawing',col, row, col+10, row+10
                draw.rectangle((col, row, col+10, row+10), fill=fill, outline=None)