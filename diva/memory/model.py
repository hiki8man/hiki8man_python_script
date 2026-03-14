from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import ctypes
import pymem
import pymem.exception
from enum import IntEnum

@dataclass
class Address(ABC):
    base_address: int
    point_offset: list["int|UIntAddress|ULongLongAddress"] = field(default_factory=list) # 指针
    address_offset: int = 0 # 指针确定好位置后偏移找到对应位置
    
    @property
    @abstractmethod
    def data_type(self) -> str: 
        return 'None'

    def _calculate_address_pymem(self, process_pymem: pymem.Pymem, process_base_address) -> int:
        if process_base_address < 0:
            real_address = self.base_address + process_pymem.base_address
        else:
            real_address = self.base_address + process_base_address

        for point_offset in self.point_offset:
            try:
                real_address = process_pymem.read_ulonglong(real_address)
                assert isinstance(real_address, int)
                
                if isinstance(point_offset, ULongLongAddress):
                    point_offset = process_pymem.read_ulonglong(point_offset.calculate_address(process_pymem))
                    
                elif isinstance(point_offset, UIntAddress):
                    point_offset = process_pymem.read_uint(point_offset.calculate_address(process_pymem))
                    
                elif isinstance(point_offset, int):
                    point_offset = point_offset

                else:
                    raise TypeError("Wrong Address Type Point")
                
                assert isinstance(point_offset, int)
                real_address += point_offset
                
            except pymem.exception.MemoryReadError:
                return 0
            
            except AssertionError:
                return 0

        return real_address + self.address_offset
    

    def calculate_address(self, offset_object: pymem.Pymem, base_address: int = -1) -> int:
        if isinstance(offset_object, pymem.Pymem):
            return self._calculate_address_pymem(offset_object, base_address)
        else:
            raise TypeError("Wrong offset_object")
        
    def __add__(self, offset:'int|Address') -> "Address":
        if isinstance(offset, Address):
            return self.__class__(self.base_address + offset.base_address)
        elif isinstance(offset, int):
            return self.__class__(self.base_address + offset)
        else:
            raise TypeError("Invalid offset type")

    def __sub__(self, offset:'int|Address') -> "Address":
        if isinstance(offset, Address):
            return self.__class__(self.base_address - offset.base_address)
        elif isinstance(offset, int):
            return self.__class__(self.base_address - offset)
        else:
            raise TypeError("Invalid offset type")

@dataclass
class UIntAddress(Address):
    @property
    def data_type(self) -> str: return "uint"

@dataclass
class ULongLongAddress(Address):
    @property
    def data_type(self) -> str: return "ulonglong"

@dataclass
class FloatAddress(Address):
    @property
    def data_type(self) -> str: return "float"

@dataclass
class BoolAddress(Address):
    @property
    def data_type(self) -> str: return "bool"

@dataclass
class StringAddress(Address):
    @property
    def data_type(self) -> str: return "string"

@dataclass
class CStringAddress(Address):
    @property
    def data_type(self) -> str: return "c-string"

class DivaString(ctypes.Structure):
    _fields_ = [("data_byte", ctypes.c_byte*16),
                ("end_point", ctypes.c_uint64),
                ("data_size", ctypes.c_uint64)]

class DivaAddress:
    class Offset:
        eden: int = int("0x105F460", 16) # 影响打歌界面切换
    
    class LastSelect:
        pvid: UIntAddress = UIntAddress(int("0x12B6350", 16))
        sort: UIntAddress = UIntAddress(int("0x12B6354", 16))
        diff_type: UIntAddress = UIntAddress(int("0x12B634C", 16))
        diff_value: UIntAddress = UIntAddress(int("0x12B635C", 16))
    
    class GameState:
        next: UIntAddress = UIntAddress(int("0xCC61098", 16)) # 6表示pv鉴赏模式，2表示选歌界面
        change: UIntAddress = UIntAddress(int("0xCC610A0", 16)) #其为二进制，01表示已完成，11表示准备跳转

    class GetSelectSong:
        playing: UIntAddress = UIntAddress(int("0x16E2BB0", 16))
        # 主用方案，需要根据是否为随机获取值，但随机值获取指针有点奇怪
        selected: UIntAddress = UIntAddress(int("0xCC5EF18", 16), [UIntAddress(int("0x6EFE8C", 16))])
        random: UIntAddress= UIntAddress(int("0xCBFA9C0", 16), [int("0x261F8", 16), 0, 0])
        # 备用方案，是不是随机都可以都在这里读，但是定位方法比较奇怪
        selected_with_random: UIntAddress = UIntAddress(int("0xCC5EF18", 16), [UIntAddress(int("0x6EFE8C", 16))], -int("0x9c8", 16))
        
    class DBInfo:
        first: ULongLongAddress = ULongLongAddress(int("0x1753818", 16), [0])
        last: ULongLongAddress = ULongLongAddress(int("0x1753820", 16), [0])
        capacity_end: ULongLongAddress = ULongLongAddress(int("0x1753828", 16), [0]) # 给出多余空间便于后续添加
        
    class DBFolderInfo:
        first: ULongLongAddress = ULongLongAddress(int("0x14AB8A0", 16), [0])
        last: ULongLongAddress = ULongLongAddress(int("0x14AB8A8", 16), [0])
        capacity_end: ULongLongAddress = ULongLongAddress(int("0x14AB8B0", 16), [0]) # 给出多余空间便于后续添加
        
    class DBLogger:
        first: ULongLongAddress = ULongLongAddress(int("0x16EBDD0", 16), [0])
        last: ULongLongAddress = ULongLongAddress(int("0x16EBDD8", 16), [0])
        capacity_end: ULongLongAddress = ULongLongAddress(int("0x16EBDE0", 16), [0]) # 给出多余空间便于后续添加

@dataclass
class NewClassicsAddress:
    class Mode:
        state: UIntAddress = UIntAddress(int("0x114F80", 16))
        
class NewClassicsStyle(IntEnum):
    ARCADE = 0
    CONSOLE = 1
    MIXED = 2
