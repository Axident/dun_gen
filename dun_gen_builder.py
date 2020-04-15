from PySide.QtCore import *
from PySide.QtGui import *
import os
import re
import time
import sys
import random
from PIL import Image, ImageDraw, ImageFont

class Cell(object):

    def __init__(self, location):
        self.direction = None
        self.space_type = None
        self.name = None
        self.color = (0,0,0)
        self.location = location
        self.north = None
        self.south = None
        self.west = None
        self.east = None
        
    def __str__(self):
        cell = 'cell @ %s type: %s, color: %s' % (self.location, self.space_type, self.color)
        for direction in ['north', 'south', 'east', 'west']:
            value = getattr(self, direction)
            if value:
                cell += " %s: %s" % (direction, value)
        return cell

class MapBuilderWorker(QThread):
    status = Signal(object)
    finished = Signal(object)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.data = []
        self.source_img = None
        self.draw = None
        self.delay = .0
        self.continue_pool = 20
        self.continue_chance = 12
        self.straight_hall_chance = 16
        self.room_count = 0
        self.recursion_safety = 0

    def generate(self):
        self.data = []
        self.room_count = 0
        self.source_img = Image.new('RGB', (1000,1000))
        self.draw = ImageDraw.Draw(self.source_img)
        for r in range(0,100):
            row = []
            for c in range(0, 100):
                cell = Cell([r,c])
                row.append(cell)
                irow = r*10
                icol = c*10
                self.draw.rectangle((icol, irow, icol+10, irow+10), fill='black', outline=(20,20,20))
            self.data.append(row)
        self.status.emit(self.source_img)
            
    def max_box(self, direction, current_location, color):
        largest_desired_room = 12
        row, column = current_location
        max_space = 1
        #print 'checking area %s of %s' % (direction, current_location)
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
                        if r_test<=0 or r_test>=99 or c_test<=0 or c_test>=99:
                            #print "box test out of bounds [%s,%s]" % (r_test, c_test)
                            return max_space - 1
                        nw = self.data[r_test][c_test]
                        if nw.space_type is not None:
                            if nw.color != color:
                                return max_space -1
            max_space += 1
        return largest_desired_room
            
    def run(self):
        #start in the center
        self.color_cell(49, 49, (200,200,200), 'hall', outline='grey')
        self.color_cell(49, 50, (200,200,200), 'hall', outline='grey')
        self.color_cell(49, 51, (200,200,200), 'hall', outline='grey')
        self.color_cell(50, 49, (200,200,200), 'hall', outline='grey')
        self.color_cell(50, 50, (200,200,200), 'hall', outline='grey')
        self.color_cell(50, 51, (200,200,200), 'hall', outline='grey')
        self.color_cell(51, 49, (200,200,200), 'hall', outline='grey')
        self.color_cell(51, 50, (200,200,200), 'hall', outline='grey')
        self.color_cell(51, 51, (200,200,200), 'hall', outline='grey')
        directions = ['north','south','west','east']
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
        for r in range(1,98):
            for c in range(1, 98):
                if self.data[r-1][c-1].space_type is None:
                    if self.data[r-1][c].space_type is None:
                        if self.data[r-1][c+1].space_type is None:
                            if self.data[r][c-1].space_type is None:
                                if self.data[r][c+1].space_type is None:
                                    if self.data[r+1][c-1].space_type is None:
                                        if self.data[r+1][c].space_type is None:
                                            if self.data[r+1][c+1].space_type is None:
                                                possibilities.append([r,c])
        
        rand_spot = random.randint(0,len(possibilities)-1)   
        row, col = possibilities[rand_spot]
        headed = directions[random.randint(0,3)]
        next_item = self.data[row][col]
        nist = "%s" % next_item.space_type
        self.color_cell(row, col, (0,0,0), 'exit', outline='yellow')
        irow = row*10
        icol = col*10
        self.draw.rectangle((icol+2, irow+2, icol+8, irow+8), fill=(255,0,0), outline='green')
        self.draw.rectangle((icol+4, irow+4, icol+6, irow+6), fill=(255,255,0), outline='blue')
        print 'setting exit @ (%d, %d)' % (row, col)
        cells_to_paint = self.create_exit_path(row, col, headed)
        while cells_to_paint is None:
            headed = directions[random.randint(0,3)]
            cells_to_paint = self.create_exit_path(row, col, headed)
        for ctp in cells_to_paint:
            row, col = ctp
            self.color_cell(row, col, (200,200,200), 'hall', outline='grey')
        if headed == "north":
            row-=1
        elif headed == "south":
            row+=1
        elif headed == "east":
            col+=1
        elif headed == "west":
            col-=1
        print 'door to exit @ (%d,%d)' % (row, col)
        self.door(row, col, headed, secret=True, auto_skip=False)
        self.finished.emit(self.source_img)
        
    def create_exit_path(self, row, col, headed):
        cells_to_paint = []
        next_item = self.data[row][col]
        nist = "%s" % next_item.space_type
        while nist in ['None', 'exit']:
            if headed == "north":
                row-=1
            elif headed == "south":
                row+=1
            elif headed == "east":
                col+=1
            elif headed == "west":
                col-=1
            if row<=0 or row>=99 or col<=0 or col>=99:
                return None
            next_item = self.data[row][col]
            nist = "%s" % next_item.space_type
            if nist == 'None':
                cells_to_paint.append([row,col])
        return cells_to_paint
        
                
    def color_cell(self, row, column, color, space_type, outline='grey'):
        nw = self.data[row][column]
        nw.space_type = space_type
        nw.color = color
        irow = row*10
        icol = column*10
        if space_type == 'room':
            color = (160,160,160)
        self.draw.rectangle((icol, irow, icol+10, irow+10), fill=color, outline=outline)
        
    def border_room(self, room, outline='white'):
        for cell in room:
            r,c = cell.location
            irow = r*10
            icol = c*10
            my_color = cell.color
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
        self.room_count+=1
        
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
            print 'skipping unnecessary %s door @ %d,%d' % (direction, row, column)
            return
        irow = row*10
        icol = column*10
        outline = (0,0,255)
        if secret:
            outline = 'red'
            setattr(cur_item, opposite, 'secret')
            setattr(last_item, direction, 'secret')
        else:
            setattr(cur_item, opposite, 'door')
            setattr(last_item, direction, 'door')
        # direction is the way you were heading when you reached this square
        if direction == 'west':
            self.draw.rectangle((icol+7, irow+2, icol+9, irow+8), fill=(0,0,0), outline=outline)
        if direction == 'east':
            self.draw.rectangle((icol+1, irow+2, icol+3, irow+8), fill=(0,0,0), outline=outline)
        if direction == 'south':
            self.draw.rectangle((icol+2, irow+1, icol+8, irow+3), fill=(0,0,0), outline=outline)
        if direction == 'north':
            self.draw.rectangle((icol+2, irow+7, icol+8, irow+9), fill=(0,0,0), outline=outline)
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
                    
    def add_random_room(self, cur_item, row, column, direction, this_type):
        red = random.randint(20,255)
        blue = random.randint(20,255)
        green = random.randint(20,255)
        color = (red,green,blue)
        roll = random.randint(1,3)
        created_room = False
        if direction == 'north':
            if roll in [1,2]:
                #handle northwest
                max_dist = self.max_box('northwest',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for r in range(row, row-distance, -1):
                        for c in range(column, column-distance, -1):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'north')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northwest')
            if roll in [1,3]:
                #handle northeast
                max_dist = self.max_box('northeast',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for r in range(row, row-distance, -1):
                        for c in range(column, column+distance):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'north')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northeast')
        if direction == 'south':
            if roll in [1,2]:
                #handle southwest
                max_dist = self.max_box('southwest',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for r in range(row, row+distance):
                        for c in range(column, column-distance, -1):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'south')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southwest')
            if roll in [1,3]:
                #handle southeast
                max_dist = self.max_box('southeast',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for r in range(row, row+distance):
                        for c in range(column, column+distance):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'south')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southeast')
        if direction == 'east':
            if roll in [1,2]:
                #handle northeast
                max_dist = self.max_box('northeast',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for c in range(column, column+distance):
                        for r in range(row, row-distance, -1):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'east')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northeast')
            if roll in [1,3]:
                #handle southeast
                max_dist = self.max_box('southeast',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for c in range(column, column+distance):
                        for r in range(row, row+distance):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'east')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southeast')
        if direction == 'west':
            if roll in [1,2]:
                #handle northwest
                max_dist = self.max_box('northwest',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for c in range(column, column-distance,-1):
                        for r in range(row, row-distance, -1):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'west')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'northwest')
            if roll in [1,3]:
                #handle southwest
                max_dist = self.max_box('southwest',cur_item.location, color)
                if max_dist == 2:
                    distance = 2
                elif max_dist > 2:
                    #distance = max(random.randint(2,max_dist),random.randint(2,max_dist))
                    distance = random.randint(2,max_dist)
                else:
                    distance = 0
                if max_dist >= 2:
                    room = []
                    for c in range(column, column-distance,-1):
                        for r in range(row, row+distance):
                            self.color_cell(r, c, color, this_type)
                            room.append(self.data[r][c])
                    self.border_room(room)
                    created_room = True
                    cur_item.space_type = this_type
                    self.door(row, column, 'west')
                
                if distance >= 3:
                    self.secret_door(row, column, distance, 'southwest')
        if self.delay:
            self.status.emit(self.source_img)
        return created_room
    
    def add_hall_left(self, row, column, direction):
        #print 'turn left'
        if direction == 'north':
            return self.add_step(row, column-1, 'west')
        elif direction == 'west':
            return self.add_step(row+1, column, 'south')
        elif direction == 'south':
            return self.add_step(row, column+1, 'east')
        elif direction == 'east':
            return self.add_step(row-1, column, 'north')
            
    def add_hall_right(self, row, column, direction):
        #print 'turn right'
        if direction == 'north':
            return self.add_step(row, column+1, 'east')
        elif direction == 'west':
            return self.add_step(row-1, column, 'north')
        elif direction == 'south':
            return self.add_step(row, column-1, 'west')
        elif direction == 'east':
            return self.add_step(row+1, column, 'south')
            
    def add_room_right(self, row, column, direction):
        if direction == 'north':
            room_item = self.data[row][column+1]
            return self.add_random_room(room_item, row, column+1, 'east', 'room')
        elif direction == 'west':
            room_item = self.data[row-1][column]
            return self.add_random_room(room_item, row-1, column, 'north', 'room')
        elif direction == 'south':
            room_item = self.data[row][column-1]
            return self.add_random_room(room_item, row, column-1, 'west', 'room')
        elif direction == 'east':
            room_item = self.data[row+1][column]
            return self.add_random_room(room_item, row+1, column, 'south', 'room')
            
    def add_room_left(self, row, column, direction):
        if direction == 'north':
            room_item = self.data[row][column-1]
            return self.add_random_room(room_item, row, column-1, 'west', 'room')
        elif direction == 'west':
            room_item = self.data[row+1][column]
            return self.add_random_room(room_item, row+1, column, 'south', 'room')
        elif direction == 'south':
            room_item = self.data[row][column+1]
            return self.add_random_room(room_item, row, column+1, 'east', 'room')
        elif direction == 'east':
            room_item = self.data[row-1][column]
            return self.add_random_room(room_item, row-1, column, 'north', 'room')
        
    def add_step(self, row, column, direction):
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
        if row<=0 or row>=99 or column<=0 or column>=99:
            #print '%sbound hall out of bounds, redirecting' % direction,
            if last_row<=0 or last_row>=99 or last_col<=0 or last_col>=99:
                return False
            #print 'attempting redirect from [%d,%d]' % (row,column)
            roll = random.randint(0,1)
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
                self.door(row, column, direction, secret=(random.randint(1,3)==1))
                return True
            return False
            
        last_item = self.data[last_row][last_col]
        if last_item.space_type == 'room':
            self.door(row, column, direction, secret=(random.randint(1,3)==1))
            
        cur_item.direction = direction
        self.color_cell(row, column, (200,200,200), 'hall', outline='grey')
        if self.delay:
            self.status.emit(self.source_img)
        time.sleep(self.delay)
        
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
            
        added_step = False
        added_room = False
        also_go_straight = True
        if random.randint(0,self.continue_pool) > self.continue_chance:
            also_go_straight = False
            
        min = 0
        if self.room_count < 4:
            min = 1
            also_go_straight = True
        roll = random.randint(min,self.straight_hall_chance)
        if roll == 1:
            #print 'turn left'
            added_step = self.add_hall_left(row, column, direction)
            if also_go_straight:
                self.add_step(next_row, next_col, direction)
        elif roll == 2:
            #print 'turn right'
            added_step = self.add_hall_right(row, column, direction)
            if also_go_straight:
                self.add_step(next_row, next_col, direction)
        elif roll == 3:
            #print 'room right'
            created = self.add_room_right(row, column, direction)
            if also_go_straight or not created:
                self.add_step(next_row, next_col, direction)
        elif roll == 4:
            #print 'room left'
            created = self.add_room_left(row, column, direction)
            if also_go_straight or not created:
                self.add_step(next_row, next_col, direction)
        else:
            #print 'step straight'
            return self.add_step(next_row, next_col, direction)
        
    def add_random_item(self, row, column, direction, space_type=None, outline=None):
        if row<=0 or row>=99 or column<=0 or column>=99:
            return False
        cur_item = self.data[row][column]
        if cur_item.space_type:
            self.door(row, column, direction, secret=True)
            return True
        if space_type:
            this_type = space_type
        else:
            roll = random.randint(0,10)
            if roll <= 8:
                this_type = 'hall'
            else:
                this_type = 'room'
        if this_type == 'room':
            self.add_random_room(cur_item, row, column, direction, this_type)
        else:
            self.add_step(row, column, direction)
        return True
        
    def stop(self):
        self.terminate()