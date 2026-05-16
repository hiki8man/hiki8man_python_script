
from dataclasses import dataclass
import math
from enum import Enum
from collections import Counter
from functools import cmp_to_key

class Shape(Enum):
    POLYGON = 0
    LINE = 1
    POINT = -1

@dataclass(frozen=True)
class Vector:
    x:float
    y:float

    def __add__(self, other) -> "Vector":
        # a + b
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        elif isinstance(other, (int, float)):
            return Vector(self.x + other, self.y + other)
        else:
            raise TypeError()
    def __sub__(self, other) -> "Vector":
        # a - b
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        elif isinstance(other, (int, float)):
            return Vector(self.x - other, self.y - other)
        else:
            raise TypeError()

    def __truediv__(self, other) -> "Vector":
        # a / b
        if isinstance(other, (int, float)):
            return Vector(self.x / other, self.y / other)
        else:
            raise TypeError()

    def dot(self, other) -> float:
        # a.b
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y
        else:
            raise TypeError()
    
    def cross(self, other) -> float:
        # a.b
        if isinstance(other, Vector):
            return self.x * other.y - self.y * other.x
        else:
            raise TypeError()
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))

def get_shape_type(multi_note: list[Vector]) -> Shape:
    same_count_dict = Counter(multi_note)

    is_line = True
    is_same = False
    diva_check = False

    note_pre2: None|Vector = multi_note[0]
    note_pre1: None|Vector = multi_note[1]

    for i in range(2, len(multi_note)):
        note_cur = multi_note[i]
        if is_line:
            vet1 = note_pre1 - note_pre2
            vet2 = note_cur - note_pre2
            is_line = (vet1.cross(vet2) == 0)
        else:
            break
        
    if len(same_count_dict) == 1:
        is_same = True
    
    if len(same_count_dict) == 2:
        diva_check = True
        single:None|Vector = None
        multi:None|Vector = None

        keys:list[Vector] = list(same_count_dict.keys())
        
        if same_count_dict[keys[0]] > same_count_dict[keys[1]] and same_count_dict[keys[1]] == 1:
            single, multi = keys[1], keys[0]
            
        elif same_count_dict[keys[0]] < same_count_dict[keys[1]] and same_count_dict[keys[0]] == 1:
            single, multi = keys[0], keys[1]

        if isinstance(single, Vector) and isinstance(multi, Vector):
            diva_check = (multi.y - single.y) <= 0

    if is_line == False and is_same == False:
        return Shape.POLYGON

    elif diva_check:
        return Shape.POLYGON

    elif is_same:
        return Shape.POINT

    else:
        return Shape.LINE

def polar_angle_sort(multi_note: list[Vector]) -> list[Vector]:
    count = len(multi_note)
    centorid = Vector(0,0)

    for note in multi_note:
        centorid = centorid + note
    centorid = centorid / count

    def sorted_func(note) -> float:
        angle = math.atan2(note.y - centorid.y, note.x - centorid.x)
        if angle < 0:
            return angle + 2 * math.pi

        return angle

    multi_note.sort(key=sorted_func) 

    return multi_note

def polar_angle_sort_cross(multi_note: list[Vector]) -> list[Vector]:
    count = len(multi_note)
    centorid = Vector(0,0)

    for note in multi_note:
        centorid = centorid + note
    centorid = centorid / count

    def cmp_cross(point_a:Vector, point_b:Vector) -> int:
        vet1:Vector = point_a - centorid
        vet2:Vector = point_b - point_a
        cross = vet1.cross(vet2)

        if cross < 0:
            return -1
        elif cross > 0:
            return 1
        else:
            return 0

    top_note = [note for note in multi_note if note.y > centorid.y]
    button_note = [note for note in multi_note if not note in top_note]

    top_note.sort(key=cmp_to_key(cmp_cross))
    button_note.sort(key=cmp_to_key(cmp_cross))

    return top_note + button_note

def multi_connect(multi_note: list[Vector]):
    # 多押连接线调用函数
    multi_count = len(multi_note)

    if multi_count == 0:
        raise ValueError("至少需要一个点")
    
    if multi_count == 1:
        return multi_note[0]
    
    if multi_count == 2:
        return multi_note

    shape_type = get_shape_type(multi_note)

    if shape_type == Shape.LINE:
        multi_note.sort(key=lambda x: (x.x, x.y))
        return multi_note

    elif shape_type == Shape.POINT:
        multi_note.append(multi_note[0])
        return multi_note

    else:
        multi_note = polar_angle_sort_cross(multi_note)
        multi_note.append(multi_note[0])
        return multi_note