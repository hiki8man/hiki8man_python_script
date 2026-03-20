from dataclasses import dataclass, field
import ctypes

from enum import IntEnum, auto

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

class Difficulty(IntEnum):
    EASY = 0
    NORMAL = 1
    HARD = 2
    EXTREME = 3
    EXEXTREME = 4
    ENCORE = 5

@dataclass(frozen=True)
class SwitchSong:
    pvid: int
    difficulty: Difficulty
    style: NewClassicsStyle = NewClassicsStyle.ARCADE

class SelectState(IntEnum):
    RANDOM_SELECL = -2
    UNKNOW_STATE = -1
    ANOTHER_MENU = 0
    ON_SELECTED = 1

    @classmethod
    def _missing_(cls, value) -> int:
        return cls.ON_SELECTED

class GameState(IntEnum):
    LOADING = 1
    INTRO = 2
    TITLE = 3
    SELECT = 5
    WATCH  = 6
    PLAYING = 7
    CUSTOMIZATION = 36
    GALLEY = 38
    MENU = 42
    SETTING = 44

class SelectSort(IntEnum):
    by_name = 0
    by_difficulty = 1
    by_chara = 2
    by_scroe = 3

class ArchiveChange(IntEnum):
    WAIT = 1
    START = 2

