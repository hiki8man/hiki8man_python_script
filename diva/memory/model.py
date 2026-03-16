from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import ctypes
import pymem
import pymem.exception
import pymem.process
from enum import IntEnum
from collections.abc import Sequence

def get_module(process_pymem:pymem.Pymem, module_name:str = ""):
        module = pymem.process.module_from_name(process_pymem.process_handle, module_name)
        return module if module else process_pymem.process_base

def get_module_address(process_pymem:pymem.Pymem, module_name:str = "") -> int:
    module = get_module(process_pymem, module_name)
    """获取模块地址，如果模块不存在返回主程序地址"""
    if module_name == "":
        return process_pymem.base_address
    for module in process_pymem.list_modules():
        if module.name == module_name:
            return module.lpBaseOfDll

    return module.lpBaseOfDll

@dataclass(frozen=True)
class StaticOffset(ABC):
    value: int
    
    def get_value(self, *args) -> int:
        return self.value

    @property
    @abstractmethod
    def use_read64(self) -> bool:
        pass

@dataclass(frozen=True)
class StaticOffset32(StaticOffset):
    def use_read64(self) -> bool:
        return False

@dataclass(frozen=True)
class StaticOffset64(StaticOffset):
    def use_read64(self) -> bool:
        return True

@dataclass(frozen=True)
class DynamicOffset(ABC):
    base: int
    offset: int = 0
    use_read64: bool = True

    def get_value(self, process_pymem: pymem.Pymem) -> int:
        return self._get_value(process_pymem)

    @abstractmethod
    def _get_value(self, process_pymem: pymem.Pymem) -> int:
        pass

@dataclass(frozen=True)
class DynamicOffset32(DynamicOffset):
    def _get_value(self, process_pymem: pymem.Pymem) -> int:
        value = process_pymem.read_uint(self.base)
        assert isinstance(value, int)
        return value + self.offset

@dataclass(frozen=True)
class DynamicOffset64(DynamicOffset):
    def _get_value(self, process_pymem: pymem.Pymem) -> int:
        value = process_pymem.read_ulonglong(self.base)
        assert isinstance(value, int)
        return value + self.offset

@dataclass(frozen=True)
class PatternScan():
    patter_bytes: bytes
    address_offset: int = 0
    
    def get_address(self, process_pymem: pymem.Pymem, _module_name: str = "") -> int:
        return_address: int = 0
        if self.patter_bytes:
            module = get_module(process_pymem, _module_name)
                
            scan_address = process_pymem.pattern_scan_module(self.patter_bytes, module)
            if isinstance(scan_address, int):
                offset = process_pymem.read_int(scan_address + self.address_offset)
                if offset and isinstance(offset, int):
                    return_address = offset + scan_address + self.address_offset + 4
    

        return 0 if return_address <= 0 else return_address
        

@dataclass(frozen=True)
class Pointer():
    base: int|PatternScan
    offset: Sequence[DynamicOffset|StaticOffset] = field(default_factory=lambda: [StaticOffset32(0)])
    finally_offset: int = 0

    def __post_init__(self):
        if isinstance(self.base, int) and self.base <= 0:
            raise ValueError("base address must be positive")

    def get_address(self, process_pymem: pymem.Pymem, _module_name: str = ""):
        base_address:int = get_module_address(process_pymem, _module_name)

        if isinstance(self.base ,int):
            finally_address = base_address + self.base
        else:
            finally_address = base_address + self.base.get_address(process_pymem)

        for offset in self.offset:
            if offset.use_read64:
                finally_address = process_pymem.read_ulonglong(finally_address)
            else:
                finally_address = process_pymem.read_uint(finally_address)
            if isinstance(finally_address, int):
                finally_address = finally_address + offset.get_value(process_pymem)
            else:
                return 0

        finally_address += self.finally_offset

        return 0 if finally_address <= 0 else finally_address
        
@dataclass(frozen=True)
class Address(ABC):
    address: int|Pointer|PatternScan
    module_name: str = ""

    def __post_init__(self):
        if isinstance(self.address, int) and self.address <= 0:
            raise ValueError("base address must be positive")

    def get_address(self, process_pymem: pymem.Pymem) -> int:
        if isinstance(self.address, int):
            base_address:int = get_module_address(process_pymem, self.module_name)
            return self.address + base_address

        elif isinstance(self.address, Pointer):
            return self.address.get_address(process_pymem, self.module_name)
        
        elif isinstance(self.address, PatternScan):
            return self.address.get_address(process_pymem, self.module_name)

        else:
            raise TypeError("address type error")

class DivaString(ctypes.Structure):
    _fields_ = [("data_byte", ctypes.c_byte*16),
                ("end_point", ctypes.c_uint64),
                ("data_size", ctypes.c_uint64)]

class DivaAddress:
    class Offset:
        eden: int = int("0x105F460", 16) # 影响打歌界面切换
    
    class LastSelect:
        pvid: Address = Address(int("0x12B6350", 16))
        sort: Address = Address(int("0x12B6354", 16))
        diff_type: Address = Address(int("0x12B634C", 16))
        diff_value: Address = Address(int("0x12B635C", 16))
    
    class GameState:
        next: Address = Address(int("0xCC61098", 16)) # 6表示pv鉴赏模式，2表示选歌界面
        change: Address = Address(int("0xCC610A0", 16)) #其为二进制，01表示已完成，11表示准备跳转

    class GetSelectSong:
        playing: Address = Address(int("0x16E2BB0", 16))
        # 主用方案，需要根据是否为随机获取值，但随机值获取指针有点奇怪
        selected: Address = Address(
            Pointer(
                int("0xCC5EF18", 16), 
                [DynamicOffset32(int("0x6EFE8C", 16))], 
            )
        )
        random: Address= Address(
            Pointer(
                int("0xCBFA9C0", 16), 
                [DynamicOffset32(int("0x6EFE8A", 16)), StaticOffset32(0), StaticOffset32(0)]
            )
        )
        # 备用方案，是不是随机都可以都在这里读，但是定位方法比较奇怪
        selected_with_random: Address = Address(
            Pointer(
                int("0xCC5EF18", 16), 
                [DynamicOffset32(int("0x6EFE8C", 16))], 
                -int("0x9c8", 16)
            )
        )
        
    class DBInfo:
        first: Address = Address(Pointer(int("0x1753818", 16)))
        last: Address = Address(Pointer(int("0x1753820", 16)))
        capacity_end: Address = Address(Pointer(int("0x1753828", 16))) # 给出多余空间便于后续添加
        
    class DBFolderInfo:
        first: Address = Address(Pointer(int("0x14AB8A0", 16)))
        last: Address = Address(Pointer(int("0x14AB8A8", 16)))
        capacity_end: Address = Address(Pointer(int("0x14AB8B0", 16))) # 给出多余空间便于后续添加
        
    class DBLogger:
        address: Address = Address(Pointer(int("0x16EBDD0", 16)))

@dataclass
class NewClassicsAddress:
    class Mode:
        pattern: bytes = b"\x74\x0B\x8B\x88....\x83\xF9\x03\x75\x02\x33\xC9\x89\x0D....\x40\x0F\xB6\xC7\x48\x8B"
        state: Address = Address(PatternScan(pattern, 17), "NewClassics.dll")
        
class NewClassicsStyle(IntEnum):
    ARCADE = 0
    CONSOLE = 1
    MIXED = 2

class SelectState(IntEnum):
    RANDOM_SELECL = -2
    UNKNOW_STATE = -1
    ANOTHER_MENU = 0
    ON_SELECTED = 1
    
    @classmethod
    def _missing_(cls, value) -> int:
        return cls.ON_SELECTED
    