try:
    from PySide.QtCore import *
    from PySide.QtGui import *
except:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    
import os
import re
import time
import sys
import random

class Cell(QGraphicsRectItem):

    def __init__(self, location, parent=None):
        super(Cell, self).__init__(None)

        self.direction = None
        self.space_type = None
        self.name = None
        self.ghost = False
        self.color = (0, 0, 0)
        self.outline = (40, 40, 40)
        self.location = location
        self.north = None
        self.south = None
        self.west = None
        self.east = None
        self.parent = parent
        self.known = False
        self.visible = True
        self.cheat = False

        self.setRect(QRect(0, 0, 10, 10))
        self.setX(self.location[0]*10 + 10)
        self.setY(self.location[1]*10 + 10)
        #self.update_tooltip()

        
    def __str__(self):
        cell = 'cell @ %s type: %s, color: %s' % (self.location, self.space_type, self.color)
        for direction in ['north', 'south', 'east', 'west']:
            value = getattr(self, direction)
            if value:
                cell += " %s: %s" % (direction, value)
        return cell

    def boundingRect(self):
        return QRect(0, 0, 10, 10)

    def update_tooltip(self):
        self.setToolTip('cell @ %s type: %s, color: %s' %
                        (self.location, self.space_type, self.color))
    def paint(self, painter, option, widget):
        painter.save()
        pen = QPen()
        pen.setColor(QColor(*self.outline))
        pen.setWidth(1)
        pen.setJoinStyle(Qt.MiterJoin)
        if not self.known and not self.cheat:
            pen.setColor(QColor(40, 40, 40))
            painter.setBrush(QColor(0, 0, 0))
        elif self.space_type == 'room':
            if self.visible or self.cheat:
                painter.setBrush(QColor(255, 255, 220))
            else:
                painter.setBrush(QColor(160, 160, 160))
            pen.setColor(QColor(120, 120, 120))
        elif self.space_type == 'hall':
            if self.visible or self.cheat:
                painter.setBrush(QColor(220, 220, 200))
            else:
                painter.setBrush(QColor(120, 120, 120))
        else:
            painter.setBrush(QColor(*self.color))
        if self.ghost:
            painter.setBrush(QColor(20, 20, 20))
            pen.setColor(QColor(30, 30, 30))
        painter.setPen(pen)
        painter.drawRect(0, 0, 10, 10)
        painter.restore()

        if not self.cheat:
            if self.ghost or not self.known:
                return

        if self.north or self.south or self.west or self.east:
            painter.save()
            if self.east in ['door', 'known_secret']:
                outline = (0, 0, 255)
                if self.east == 'known_secret':
                    outline = (150, 0, 150)
                painter.setPen(QPen(QBrush(QColor(*outline)), 4))
                painter.drawLine(QPoint(8, 2), QPoint(8, 8))
                painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
                painter.drawLine(QPoint(9, 0), QPoint(9, 10))
                painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
                painter.drawLine(QPoint(10, 0), QPoint(10, 10))
            if self.west in ['door', 'known_secret']:
                outline = (0, 0, 255)
                if self.west == 'known_secret':
                    outline = (150, 0, 150)
                painter.setPen(QPen(QBrush(QColor(*outline)), 4))
                painter.drawLine(QPoint(2, 2), QPoint(2, 8))
                painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
                painter.drawLine(QPoint(0, 0), QPoint(0, 10))
                painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
                painter.drawLine(QPoint(1, 0), QPoint(1, 10))
            if self.north in ['door', 'known_secret']:
                outline = (0, 0, 255)
                if self.north == 'known_secret':
                    outline = (150, 0, 150)
                painter.setPen(QPen(QBrush(QColor(*outline)), 4))
                painter.drawLine(QPoint(2, 2), QPoint(8, 2))
                painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
                painter.drawLine(QPoint(0, 0), QPoint(9, 0))
                painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
                painter.drawLine(QPoint(0, 1), QPoint(9, 1))
            if self.south in ['door', 'known_secret']:
                outline = (0, 0, 255)
                if self.south == 'known_secret':
                    outline = (150, 0, 150)
                painter.setPen(QPen(QBrush(QColor(*outline)), 4))
                painter.drawLine(QPoint(2, 8), QPoint(8, 8))
                painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
                painter.drawLine(QPoint(0, 9), QPoint(10, 9))
                painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
                painter.drawLine(QPoint(0, 10), QPoint(10, 10))
            painter.restore()

        north = None
        if self.location[1] > 0:
            north = self.parent.data[self.location[1]-1][self.location[0]]
        south = None
        if self.location[1] < 98:
            south = self.parent.data[self.location[1]+1][self.location[0]]
        west = None
        if self.location[0] > 0:
            west = self.parent.data[self.location[1]][self.location[0]-1]
        east = None
        if self.location[0] < 98:
            east = self.parent.data[self.location[1]][self.location[0]+1]

        # is north wall?
        if self.location[1] == 0 or (north and north.color != self.color):
            painter.save()
            painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
            painter.drawLine(QPoint(0, 0), QPoint(9, 0))
            painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
            painter.drawLine(QPoint(0, 1), QPoint(9, 1))
            painter.restore()
        # is west wall?
        if self.location[0] == 0 or (west and west.color != self.color):
            painter.save()
            painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
            painter.drawLine(QPoint(0, 0), QPoint(0, 10))
            painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
            painter.drawLine(QPoint(1, 0), QPoint(1, 10))
            painter.restore()
        # is east wall?
        if self.location[0] == 99 or (east and east.color != self.color):
            painter.save()
            painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
            painter.drawLine(QPoint(9, 0), QPoint(9, 10))
            painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
            painter.drawLine(QPoint(10, 0), QPoint(10, 10))
            painter.restore()
        # is south wall?
        if self.location[1] == 99 or (south and south.color != self.color):
            painter.save()
            painter.setPen(QPen(QBrush(QColor(255, 255, 255)), 1))
            painter.drawLine(QPoint(0, 9), QPoint(10, 9))
            painter.setPen(QPen(QBrush(QColor(0, 0, 0)), 1))
            painter.drawLine(QPoint(0, 10), QPoint(10, 10))
            painter.restore()

        if self.space_type == 'exit':
            painter.save()
            painter.setBrush(QColor(250, 10, 250))
            painter.drawRect(1, 1, 7, 7)
            painter.setBrush(QColor(10, 250, 10))
            painter.drawRect(3, 3, 3, 3)
            painter.restore()



class MapBuilderWorker(QThread):
    status = Signal(object)
    finished = Signal(object)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.data = []
        self.delay = 0
        self.continue_pool = 20
        self.continue_chance = 12
        self.straight_hall_chance = 16
        self.room_count = 0
        self.recursion_safety = 0
        self.parent = parent

    def generate(self):
        self.data = []
        self.room_count = 0
        for r in list(range(0, 100)):
            row = []
            for c in list(range(0, 100)):
                cell = Cell([c, r], parent=self.parent)
                row.append(cell)
            self.data.append(row)
        self.status.emit(self.data)
            
    def max_box(self, direction, current_location, color):
        largest_desired_room = 12
        column, row = current_location
        max_space = 1
        non_empty_cells = 0
        #print('checking area %s of %s' % (direction, current_location))
        while max_space <= largest_desired_room:
            for value in list(range(1, max_space)):
                if direction == "northwest":
                    r_test = row - value
                    c_test = column - value
                elif direction == "northeast":
                    r_test = row - value
                    c_test = column + value
                elif direction == "southwest":
                    r_test = row + value
                    c_test = column - value
                elif direction == "southeast":
                    r_test = row + value
                    c_test = column + value
                if r_test <= 0 or r_test >= 99 or c_test <= 0 or c_test >= 99:
                    #print("box test out of bounds [%s,%s]" % (r_test, c_test))
                    return max_space - 1
                test_cells = [self.data[r_test][c_test],
                              self.data[row][c_test],
                              self.data[r_test][column]]
                for test_cell in test_cells:
                    if getattr(test_cell, 'space_type'):
                        non_empty_cells += 1
                        if test_cell.color != color:
                            #print('stopping: room would collide with %s' % test_cell)
                            return max_space - 1
                #else:
                #    print('entering empty cell %s' % test_cell)
            max_space += 1
        #print('overlapping %d cells' % non_empty_cells)
        return largest_desired_room
            
    def run(self):
        #start in the center
        self.color_cell(49, 49, (200, 200, 200), 'hall')
        self.color_cell(49, 50, (200, 200, 200), 'hall')
        self.color_cell(49, 51, (200, 200, 200), 'hall')
        self.color_cell(50, 49, (200, 200, 200), 'hall')
        self.color_cell(50, 50, (200, 200, 200), 'hall')
        self.color_cell(50, 51, (200, 200, 200), 'hall')
        self.color_cell(51, 49, (200, 200, 200), 'hall')
        self.color_cell(51, 50, (200, 200, 200), 'hall')
        self.color_cell(51, 51, (200, 200, 200), 'hall')
        directions = ['north', 'south', 'west', 'east']
        random.shuffle(directions)
        for d in directions:
            if d == 'north':
                # from the center build north:
                self.add_random_item(48, 50, 'north', space_type='hall')
            if d == 'south':
                # from the center build south:
                self.add_random_item(52, 50, 'south', space_type='hall')
            if d == 'west':
                # from the center build west:
                self.add_random_item(50, 48, 'west', space_type='hall')
            if d == 'east':
                # from the center build east:
                self.add_random_item(50, 52, 'east', space_type='hall')
        
        #random exit must be surrounded by empty space:
        possibilities = []
        for r in range(1, 98):
            for c in range(1, 98):
                if self.data[r-1][c-1].space_type is None:
                    if self.data[r-1][c].space_type is None:
                        if self.data[r-1][c+1].space_type is None:
                            if self.data[r][c-1].space_type is None:
                                if self.data[r][c+1].space_type is None:
                                    if self.data[r+1][c-1].space_type is None:
                                        if self.data[r+1][c].space_type is None:
                                            if self.data[r+1][c+1].space_type is None:
                                                possibilities.append([r, c])
        
        rand_spot = random.randint(0,len(possibilities)-1)   
        erow, ecol = possibilities[rand_spot]
        headed = directions[random.randint(0, 3)]
        self.color_cell(erow, ecol, (0, 0, 0), 'exit')
        #print('setting exit @ (%d, %d)' % (erow, ecol))
        cells_to_paint = self.create_exit_path(erow, ecol, headed)
        while cells_to_paint is None:
            headed = directions[random.randint(0,3)]
            cells_to_paint = self.create_exit_path(erow, ecol, headed)
        for ctp in cells_to_paint:
            row, col = ctp
            self.color_cell(row, col, (2, 2, 2), 'room')  # hallway that draws separate
        if headed == "north":
            row-=1
        elif headed == "south":
            row+=1
        elif headed == "east":
            col+=1
        elif headed == "west":
            col-=1
        #print('door to exit @ (%d,%d)' % (row, col))
        self.door(row, col, headed, secret=True, auto_skip=False)
        self.finished.emit(self.data[erow][ecol])
        
    def create_exit_path(self, row, col, headed):
        cells_to_paint = []
        next_item = self.data[row][col]
        nist = "%s" % next_item.space_type
        while nist in ['None', 'exit']:
            if headed == "north":
                row -= 1
            elif headed == "south":
                row += 1
            elif headed == "east":
                col += 1
            elif headed == "west":
                col -= 1
            if row <= 0 or row >= 99 or col <= 0 or col >= 99:
                return None
            next_item = self.data[row][col]
            nist = "%s" % next_item.space_type
            if nist == 'None':
                cells_to_paint.append([row, col])
        return cells_to_paint

    def color_cell(self, row, column, color, space_type):
        try:
            this_cell = self.data[row][column]
        except:
            print('cannot color missing cell at %d, %d' % (row, column))
            return None
        setattr(this_cell, 'space_type', space_type)
        setattr(this_cell, 'color', color)
        if self.delay:
            this_cell.cheat = True
            time.sleep(self.delay)
        this_cell.update()
        #this_cell.update_tooltip()
        self.parent.map_scene.update()
        return this_cell

    def door(self, row, column, direction, secret=False, other_side=False, auto_skip=True):
        cur_item = self.data[row][column]
        cur_color = cur_item.color
        last_row = row
        last_col = column
        if direction == 'north':
            opposite = 'south'
            last_row += 1
        elif direction == 'south':
            opposite = 'north'
            last_row -= 1
        elif direction == 'west':
            opposite = 'east'
            last_col += 1
        elif direction == 'east':
            opposite = 'west'
            last_col -= 1
        last_item = self.data[last_row][last_col]
        last_color = last_item.color
        if cur_color == last_color and auto_skip:
            #print('skipping unnecessary %s door @ %d,%d' % (direction, row, column))
            return
        if secret:
            setattr(cur_item, opposite, 'secret')
            setattr(last_item, direction, 'secret')
        else:
            setattr(cur_item, opposite, 'door')
            setattr(last_item, direction, 'door')
        # direction is the way you were heading when you reached this square
        if not other_side:
            self.door(last_row, last_col, opposite, secret=secret, other_side=True)
        
        
    def secret_door(self, row, column, wall_length, direction):
        max_range = 4
        wall = random.randint(1,max_range)        
        if direction == 'northwest':
            if wall in [1,2,3]:
                #west wall
                where = random.randint(row-wall_length+1, row)
                self.add_random_item(where, column-wall_length, 'west')
            if wall in [1,2,4]:
                #north wall
                where = random.randint(column-wall_length+1, column)
                self.add_random_item(row-wall_length, where, 'north')
        if direction == 'northeast':
            if wall in [1,2,3]:
                #east wall
                where = random.randint(row-wall_length+1, row)
                self.add_random_item(where, column+wall_length, 'east')
            if wall in [1,2,4]:
                #north wall
                where = random.randint(column, column+wall_length-1)
                self.add_random_item(row-wall_length, where, 'north')
        if direction == 'southwest':
            if wall in [1,2,3]:
                #south wall
                where = random.randint(column-wall_length+1, column)
                self.add_random_item(row+wall_length, where, 'south')
            if wall in [1,2,4]:
                #west wall
                where = random.randint(row, row+wall_length-1)
                self.add_random_item(where, column-wall_length, 'west')
        if direction == 'southeast':
            if wall in [1,2,3]:
                #east wall
                where = random.randint(row, row+wall_length-1)
                self.add_random_item(where, column+wall_length, 'east')
            if wall in [1,2,4]:
                #south wall
                where = random.randint(column, column+wall_length-1)
                self.add_random_item(row+wall_length, where, 'south')
                    
    def add_random_room(self, cur_item, row, column, direction):
        #print('adding room @ %s:%s' % (row, column))
        red = random.randint(20, 255)
        blue = random.randint(20, 255)
        green = random.randint(20, 255)
        color = (red, green, blue)
        roll = random.randint(1,3)
        created_room = False
        if direction == 'north':
            if roll in [1,2]:
                #handle northwest
                max_dist = self.max_box('northwest', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for r in range(row, row-distance, -1):
                        for c in range(column, column-distance, -1):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'north')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northwest')

            if roll in [1,3]:
                #handle northeast
                max_dist = self.max_box('northeast', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for r in range(row, row-distance, -1):
                        for c in range(column, column+distance):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'north')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northeast')

        if direction == 'south':
            if roll in [1,2]:
                #handle southwest
                max_dist = self.max_box('southwest', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for r in range(row, row+distance):
                        for c in range(column, column-distance, -1):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'south')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southwest')

            if roll in [1,3]:
                #handle southeast
                max_dist = self.max_box('southeast', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for r in range(row, row+distance):
                        for c in range(column, column+distance):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'south')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southeast')

        if direction == 'east':
            if roll in [1,2]:
                #handle northeast
                max_dist = self.max_box('northeast', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for c in range(column, column+distance):
                        for r in range(row, row-distance, -1):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'east')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northeast')

            if roll in [1,3]:
                #handle southeast
                max_dist = self.max_box('southeast', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for c in range(column, column+distance):
                        for r in range(row, row+distance):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'east')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southeast')

        if direction == 'west':
            if roll in [1,2]:
                #handle northwest
                max_dist = self.max_box('northwest', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for c in range(column, column-distance, -1):
                        for r in range(row, row-distance, -1):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'west')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northwest')

            if roll in [1,3]:
                #handle southwest
                max_dist = self.max_box('southwest', cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    distance = random.randint(2, max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    for c in range(column, column-distance, -1):
                        for r in range(row, row+distance):
                            self.color_cell(r, c, color, 'room')
                    created_room = True
                    setattr(cur_item, 'space_type', 'room')
                    self.door(row, column, 'west')
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southwest')

        if created_room:
            self.room_count += 1
        return created_room
    
    def add_hall_left(self, row, column, direction):
        if direction == 'north' and column > 0:
            return self.add_step(row, column-1, 'west')
        elif direction == 'west' and row < 99:
            return self.add_step(row+1, column, 'south')
        elif direction == 'south' and column < 99:
            return self.add_step(row, column+1, 'east')
        elif direction == 'east' and row > 0:
            return self.add_step(row-1, column, 'north')
        return False
            
    def add_hall_right(self, row, column, direction):
        if direction == 'north' and column < 99:
            return self.add_step(row, column+1, 'east')
        elif direction == 'west' and row > 0:
            return self.add_step(row-1, column, 'north')
        elif direction == 'south' and column > 0:
            return self.add_step(row, column-1, 'west')
        elif direction == 'east' and row < 99:
            return self.add_step(row+1, column, 'south')
        return False
            
    def add_room_right(self, row, column, direction):
        if direction == 'north' and column < 97:
            room_item = self.data[row][column+1]
            return self.add_random_room(room_item, row, column+1, 'east')
        elif direction == 'west' and row > 2:
            room_item = self.data[row-1][column]
            return self.add_random_room(room_item, row-1, column, 'north')
        elif direction == 'south' and column > 2:
            room_item = self.data[row][column-1]
            return self.add_random_room(room_item, row, column-1, 'west')
        elif direction == 'east' and row < 97:
            room_item = self.data[row+1][column]
            return self.add_random_room(room_item, row+1, column, 'south')
        return False
            
    def add_room_left(self, row, column, direction):
        if direction == 'north' and column > 2:
            room_item = self.data[row][column-1]
            return self.add_random_room(room_item, row, column-1, 'west')
        elif direction == 'west' and row < 97:
            room_item = self.data[row+1][column]
            return self.add_random_room(room_item, row+1, column, 'south')
        elif direction == 'south' and column < 97:
            room_item = self.data[row][column+1]
            return self.add_random_room(room_item, row, column+1, 'east')
        elif direction == 'east' and row > 2:
            room_item = self.data[row-1][column]
            return self.add_random_room(room_item, row-1, column, 'north')
        return False
        
    def add_step(self, row, column, direction):
        # print('adding step @ %s:%s' % (row, column))
        last_row = row
        last_col = column
        if direction == 'north':
            last_row += 1
        elif direction == 'south':
            last_row -= 1
        elif direction == 'west':
            last_col += 1
        elif direction == 'east':
            last_col -= 1
        if row <= 0 or row >= 99 or column <= 0 or column >= 99:
            #print '%sbound hall out of bounds, redirecting' % direction,
            if last_row <= 0 or last_row >= 99 or last_col <= 0 or last_col >= 99:
                return False
            #print 'attempting redirect from [%d,%d]' % (row,column)
            roll = random.randint(0, 1)
            self.recursion_safety += 1
            if self.recursion_safety > 3:
                roll = 2
            if roll == 0:
                if not self.add_hall_left(last_row, last_col, direction):
                    return self.add_hall_right(last_row, last_col, direction)
            elif roll == 1:
                if not self.add_hall_right(last_row, last_col, direction):
                    return self.add_hall_left(last_row, last_col, direction)
            return False
        self.recursion_safety = 0
            
        cur_item = self.data[row][column]
        if cur_item.space_type:
            if cur_item.space_type == 'room':
                self.door(row, column, direction, secret=(random.randint(1, 3) == 1))
                return True
            return False
            
        last_item = self.data[last_row][last_col]
        if last_item.space_type == 'room':
            self.door(row, column, direction, secret=(random.randint(1, 3) == 1))
            
        cur_item.direction = direction
        self.color_cell(row, column, (200, 200, 200), 'hall')
        self.parent.map_view.centerOn(cur_item)
        
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

        also_go_straight = True
        if random.randint(0, self.continue_pool) > self.continue_chance:
            also_go_straight = False
            
        min_roll = 0
        if self.room_count < 4:
            min_roll = 1
            also_go_straight = True
        roll = random.randint(min_roll, self.straight_hall_chance)
        if roll == 1:
            self.add_hall_left(row, column, direction)
            if also_go_straight:
                self.add_step(next_row, next_col, direction)
        elif roll == 2:
            self.add_hall_right(row, column, direction)
            if also_go_straight:
                self.add_step(next_row, next_col, direction)
        elif roll == 3:
            created = self.add_room_right(row, column, direction)
            if also_go_straight or not created:
                self.add_step(next_row, next_col, direction)
        elif roll == 4:
            created = self.add_room_left(row, column, direction)
            if also_go_straight or not created:
                self.add_step(next_row, next_col, direction)
        else:
            return self.add_step(next_row, next_col, direction)
        
    def add_random_item(self, row, column, direction, space_type=None):
        if row <= 0 or row >= 99 or column <= 0 or column >= 99:
            return False
        cur_item = self.data[row][column]
        if cur_item.space_type:
            self.door(row, column, direction, secret=True)
            return True
        if space_type:
            this_type = space_type
        else:
            roll = random.randint(0, 10)
            if roll <= 8:
                this_type = 'hall'
            else:
                this_type = 'room'
        if this_type == 'room':
            self.add_random_room(cur_item, row, column, direction)
        else:
            self.add_step(row, column, direction)
        return True
        
    def stop(self):
        self.terminate()
