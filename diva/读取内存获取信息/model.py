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

class GameDifficulty(IntEnum):
    EASY = 0
    NORMAL = 1
    HARD = 2
    EXTREME = 3
    ENCORE = 4
    
class StoredDifficulty(IntEnum):
    EASY = 0
    NORMAL = 1
    HARD = 2
    EXTREME = 3
    EXEXTREME = 4

    @classmethod
    def get_selected_difficulty(cls, type: int, is_ex: bool) -> "StoredDifficulty":
 
        match type:
            case GameDifficulty.EASY:
                return cls.EASY
            case GameDifficulty.NORMAL:
                return cls.NORMAL
            case GameDifficulty.HARD:
                return cls.HARD
            case GameDifficulty.EXTREME:
                return cls.EXEXTREME if is_ex else cls.EXTREME
            case GameDifficulty.ENCORE:
                raise ValueError("Encore is not support on MM+")
            case _:
                raise ValueError("Unknown difficulty")
        pass    

@dataclass(frozen=True)
class SwitchSong:
    pvid: int
    difficulty: StoredDifficulty
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

