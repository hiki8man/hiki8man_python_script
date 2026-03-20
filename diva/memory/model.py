from dataclasses import dataclass, field
import ctypes

from enum import IntEnum

class DivaString(ctypes.Structure):
    _fields_ = [("data_byte", ctypes.c_byte*16),
                ("end_point", ctypes.c_uint64),
                ("data_size", ctypes.c_uint64)]

        
class NewClassicsStyle(IntEnum):
    UNKNOW = -1
    ARCADE = 0
    CONSOLE = 1
    MIXED = 2

    @classmethod
    def _missing_(cls, value) -> int:
        return cls.UNKNOW

class SelectState(IntEnum):
    RANDOM_SELECL = -2
    UNKNOW_STATE = -1
    ANOTHER_MENU = 0
    ON_SELECTED = 1
    
    @classmethod
    def _missing_(cls, value) -> int:
        return cls.ON_SELECTED

class Difficulty(IntEnum):
    EASY = 0
    NORMAL = 1
    HARD = 2
    EXTREME = 3
    ENCORE = 4
    EXEXTREME = 5

@dataclass(frozen=True)
class SwitchSong:
    pv_id: int
    style: NewClassicsStyle
    difficulty: int