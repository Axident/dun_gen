try:
    from PySide.QtCore import *
    from PySide.QtGui import *
except:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    
import time
import random

class Projectile(QGraphicsEllipseItem):
    def __init__(self, location, tile_color, direction, parent=None):
        super(Projectile, self).__init__(None)
        self.direction = direction
        self.parent = parent
        self.tile_color = tile_color
        self.active = True
        self.location = location
        self.setX(self.location[1]*10+10)
        self.setY(self.location[0]*10+10)

        self.adapter = MoveAdapter(self.parent, self)
        self.animation = QPropertyAnimation(self.adapter, QByteArray(b"location"))
        
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
        return [next_row, next_col]
        #self.setX(self.location[1]*10+10)
        #self.setY(self.location[0]*10+10)

    def paint(self, painter, option, widget):
        if self.active:
            painter.save()
            pen = QPen()
            pen.setColor(QColor(255, 255, 0))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(255, 100, 0)))
            if self.direction in ['north', 'south']:
                painter.drawEllipse(QPoint(5, 5), 2, 4)
            else:
                painter.drawEllipse(QPoint(5, 5), 4, 2)
            painter.restore()

class BulletTimeWorker(QThread):
    status = Signal(object)
    finished = Signal(object)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent

    def run(self):
        while len(self.parent.projectiles):
            time.sleep(.05)
            self.status.emit(None)
        self.finished.emit(None)
        
    def stop(self):
        self.terminate()

class MoveAdapter(QObject):
    def __init__(self, parent, object_to_animate, center=False):
        super(MoveAdapter, self).__init__()
        self.object_to_animate = object_to_animate
        self.parent = parent
        self.center = center

    def get_pos(self):
        return self.object_to_animate.pos

    def set_pos(self, pos):
        self.object_to_animate.setX(pos.y())
        self.object_to_animate.setY(pos.x())
        self.object_to_animate.update()
        if self.center:
            self.parent.map_view.centerOn(self.object_to_animate)
        self.parent.map_scene.update()

    location = Property(QPoint, get_pos, set_pos)

class Monster(QGraphicsEllipseItem):
    def __init__(self, data, parent):
        super(Monster, self).__init__(None)
        self.data = data
        self.parent = parent
        self.direction = None
        
        location = self.set_start_location()
        self.location = location
        self.used_door = False
        self.next_location = location
        self.desired_location = location
        self.current_path = []
        self.color = (200, 200, 200)
        self.alive = True
        self.visible = False
        self.prey_location = [50,50]
        self.prey_status = 'alive'
        self.hunter_path = None
        self.known = []
        self.looted = False
        self.current_space_type = None
        self.setX(self.location[1]*10+10)
        self.setY(self.location[0]*10+10)

        self.adapter = MoveAdapter(self.parent, self)
        
    def __str__(self):
        return 'beast @ %s direction: %s, headed_to: %s' % (self.location, self.direction, self.desired_location)

    def paint(self, painter, option, widget):
        if self.visible:
            painter.save()
            pen = QPen()
            pen.setColor(QColor(0, 200, 0))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(0, 100, 200)))
            painter.drawEllipse(QPoint(5, 5), 4, 4)
            painter.restore()
            if self.alive:
                painter.save()
                pen.setColor(QColor(0, 0, 0))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(255, 255, 50)))
                painter.drawEllipse(QPoint(3, 4), 1, 1)
                painter.drawEllipse(QPoint(7, 4), 1, 1)
                painter.restore()
            if self.looted:
                painter.save()
                pen = QPen()
                pen.setColor(QColor(60, 0, 60))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(0, 0, 80)))
                painter.drawEllipse(QPoint(5, 5), 4, 4)
                painter.restore()
        
    def set_start_location(self):
        room_cells = []
        for r in range(0, 99):
            for c in range(0, 99):
                cell = self.data[r][c]
                if cell.space_type == 'room':
                    room_cells.append(cell)
        i = random.randint(0, len(room_cells)-1)
        self.current_space_type = room_cells[i].space_type
        return [room_cells[i].location[1], room_cells[i].location[0]]

    def move(self, prey_location, prey_alive):
        self.prey_status = prey_alive
        if self.location not in self.known:
            self.known.append(self.location)
        self.prey_location = prey_location
        next_row, next_col = self.location
        if len(self.current_path) == 0:
            #print "beast reached goal"
            self.hunter_path = None
            self.new_desired_location()
            if not self.hunter_path:
                # check for doors
                directions = []
                item = self.data[next_row][next_col]
                for d in ['north', 'south', 'east', 'west']:
                    value = getattr(item, d)
                    if value:
                        directions.append(d)
                # if there's a door, consider using it
                if directions and not self.used_door:
                    i = 0
                    self.used_door = True
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
                    self.used_door = False
            else:
                self.used_door = True
                self.current_path = self.direct_hunter_path()
            
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
        return self.location
        #self.setX(self.location[1]*10+10)
        #self.setY(self.location[0]*10+10)
        
    def direct_hunter_path(self):
        start = self.hunter_path[0]
        sr, sc = start
        start_cell = self.data[sr][sc]
        if start_cell.space_type == 'hall':
            return self.hunter_path
        end = self.hunter_path[-1]
        er, ec = end
        if sr == er:
            return self.hunter_path
        elif sc == ec:
            return self.hunter_path
        new_path = [[sr, sc]]
        if sr > er and sc > ec:
            #northwest
            while sr > er and sc > ec:
                sr -= 1
                sc -= 1
                new_path.append([sr,sc])
            while [sr, sc] != end:
                if sr == er:
                    sc-=1
                elif sc == ec:
                    sr-=1
                new_path.append([sr,sc])
        elif sr > er and sc < ec:
            #northeast
            while sr > er and sc < ec:
                sr -= 1
                sc += 1
                new_path.append([sr,sc])
            while [sr, sc] != end:
                if sr == er:
                    sc+=1
                elif sc == ec:
                    sr-=1
                new_path.append([sr,sc])
        elif sr < er and sc < ec:
            #southeast
            while sr < er and sc < ec:
                sr += 1
                sc += 1
                new_path.append([sr,sc])
            while [sr, sc] != end:
                if sr == er:
                    sc+=1
                elif sc == ec:
                    sr+=1
                new_path.append([sr,sc])
        elif sr < er and sc > ec:
            #southwest
            while sr < er and sc > ec:
                sr += 1
                sc -= 1
                new_path.append([sr,sc])
            while [sr, sc] != end:
                if sr == er:
                    sc-=1
                elif sc == ec:
                    sr+=1
                new_path.append([sr,sc])
        return new_path
            
    def new_desired_location(self):
        #print 'setting new desired location'
        self.hunter_path = None
        desired_locations = set()
        row, column = self.location
        item = self.data[row][column]
        paths = []
        for direction in ['north', 'south', 'west', 'east']:
            path = self.look(row, column, direction, path = [[row, column]])
            if self.hunter_path:
                self.current_path = self.hunter_path
                self.desired_location = self.current_path[-1]
                return
            paths.append(path)
            if len(path) > 2:
                for cell in range(2,len(path)):
                    branch = path[:cell]
                    b_row, b_col = path[cell-1]
                    if direction in ['north', 'south']:
                        for sub_d in ['east', 'west']:
                            test = self.look(b_row, b_col, sub_d, path=[])
                            if self.hunter_path:
                                self.hunter_path = branch + test  
                                self.current_path = self.hunter_path
                                self.desired_location = self.current_path[-1]
                                return
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
                            if self.hunter_path:
                                self.hunter_path = branch + test  
                                self.current_path = self.hunter_path
                                self.desired_location = self.current_path[-1]
                                return
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
            
    def look(self, row, column, direction, path=[]):
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
        if next_row <= 0 or next_row >= 99 or next_col <= 0 or next_col >= 99:
            return path
        next_item = self.data[next_row][next_col]
        if next_item.space_type and next_item.color == self.color:
            path.append([next_row, next_col])
            if [next_row, next_col] == self.prey_location:
                if self.prey_status:
                    print("I SEE YOU!")
                    self.hunter_path = path
                    return path
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
        self.parent = parent
        self.data = data

    def run(self):
        alive_count = len(self.beasts)
        while len(self.parent.monsters):
            time.sleep(.25)
            self.status.emit(None)
        self.finished.emit(None)
        
    def stop(self):
        self.terminate()
