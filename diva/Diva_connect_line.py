from dataclasses import dataclass
import math
from enum import Enum
from collections import Counter
from functools import cmp_to_key

class Shape(Enum):
    POINT = 0
    LINE = 1
    POLYGON = 2

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
    if len(multi_note) == 0:
        raise ValueError()
    
    if len(multi_note) == 1:
        return Shape.POINT
    
    if len(multi_note) == 2:
        return Shape.LINE

    def diva_polygon_check(same_count_dict:dict[Vector, int]) -> bool:
        # 只有在所有点共线的时候才会调用函数
        top_note:Vector    = max(same_count_dict.keys(), key= lambda p: p.y)
        bottom_note:Vector = min(same_count_dict.keys(), key= lambda p: p.y)

        # 判断是否是垂直线
        if top_note.x == bottom_note.x:
            return False
        # 判断是否是水平线
        if top_note.y == bottom_note.y:
            return False
        # 处理Diva的情况
        if same_count_dict[top_note] > same_count_dict[bottom_note]:
            return False

        return True

    is_dot: bool = False
    is_polygon: bool = False
    is_diva_polygon: bool = False

    note_pre2: None|Vector = multi_note[0]
    note_pre1: None|Vector = multi_note[1]

    for i in range(2, len(multi_note)):
        note_cur = multi_note[i]
        if is_polygon == False:
            vet1 = note_pre1 - note_pre2
            vet2 = note_cur - note_pre2
            is_polygon = (vet1.cross(vet2) != 0)
        else:
            return Shape.POLYGON

    same_count_dict = Counter(multi_note)

    if len(same_count_dict) == 1:
        is_dot = True
    
    elif len(same_count_dict) < len(multi_note):
        is_diva_polygon = diva_polygon_check(same_count_dict)

    if is_diva_polygon:
        return Shape.POLYGON

    elif is_dot:
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
    bottom_note = [note for note in multi_note if not note in top_note]

    top_note.sort(key=cmp_to_key(cmp_cross))
    bottom_note.sort(key=cmp_to_key(cmp_cross))

    return top_note + bottom_note

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