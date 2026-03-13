import pymem
import pymem.exception
import psutil
from pathlib import Path
from dataclasses import dataclass
from typing import ClassVar
from functools import wraps
from abc import ABC, abstractmethod

@dataclass
class Address(ABC):
    address: int

    @property
    @abstractmethod
    def data_type(self) -> str: return 'None'

    def __add__(self, offset:'int|Address') -> "Address":
        if isinstance(offset, Address):
            return self.__class__(self.address + offset.address)
        elif isinstance(offset, int):
            return self.__class__(self.address + offset)
        else:
            raise TypeError("Invalid offset type")

    def __sub__(self, offset:'int|Address') -> "Address":
        if isinstance(offset, Address):
            return self.__class__(self.address - offset.address)
        elif isinstance(offset, int):
            return self.__class__(self.address - offset)
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
    def data_type(self) -> str: return "cstring"

@dataclass
class DivaAddress:
    eden_offset: int = int("0x105F460", 16) # 影响打歌界面切换
    last_select_pvid: UIntAddress = UIntAddress(int("0x12B6350", 16))

    last_select_sort: UIntAddress = UIntAddress(int("0x12B6354", 16))
    last_select_diff_type: UIntAddress = UIntAddress(int("0x12B634C" , 16))
    last_select_diff_value: UIntAddress = UIntAddress(int("0x12B635C" , 16))

    next_state: ULongLongAddress = ULongLongAddress(int("0xCC61098", 16)) # 6表示pv鉴赏模式，2表示选歌界面
    change_state: ULongLongAddress = ULongLongAddress(int("0xCC610A0", 16)) #其为二进制，01表示已完成，11表示准备跳转

    select_id_base_address: ULongLongAddress = ULongLongAddress(int("0xCC5EF18", 16)) # pvid的基址
    select_id_offset: int = int("0x000258DC", 16)

    now_playing_address: UIntAddress = UIntAddress(int("0x16E2BB0", 16))

    db_first_address: ULongLongAddress = ULongLongAddress(int("0x1753818", 16))
    db_last_address: ULongLongAddress = ULongLongAddress(int("0x1753820", 16))
    db_end_address: ULongLongAddress = ULongLongAddress(int("0x1753828", 16)) # 给出多余空间便于后续添加

@dataclass
class NewClassAddress:
    pass

class MemoryManager(pymem.Pymem):
    def __init__(self, program_name: str|int|None = None) -> None:
        super().__init__()
        self.program_name:str|int|None = program_name
        self.open_program()

    def open_program(self, program_name: str|int|None = None) -> None:
        if isinstance(program_name, int) and program_name > 0:
            self.program_name = program_name
        elif program_name and program_name != self.program_name:
            self.program_name = program_name

        if isinstance(self.program_name, int):
            self.open_process_from_id(self.program_name)
        elif isinstance(self.program_name, str):
            self.open_process_from_name(self.program_name)

    @property
    def is_running(self) -> bool:
        return self._check_is_running()

    def _check_is_running(self) -> bool:
        return isinstance(self.process_id, int) and psutil.pid_exists(self.process_id)

    def get_address_from_ptr(self, base_address: int, offset_list: list[int]|int) -> int:

        if isinstance(offset_list, int):
            offset_list = [offset_list]

        for offset in offset_list:
            try:
                address = self.read_ulonglong(base_address)
                assert isinstance(address, int)
                base_address = address + offset
            except pymem.exception.MemoryReadError:
                return 0

        return base_address

    def read_cstring(self, address: int) -> str:
        c_string = bytes()
        currect_address = address
        while True:
            try:
                char:bytes = self.read_bytes(currect_address,1)
                if char == b"\x00": break
                c_string += char
                currect_address += 1
            except pymem.exception.MemoryReadError:
                break
        return c_string.decode()


class DivaMemoryManager(MemoryManager):
    def __init__(self):
        super().__init__("DivaMegaMix.exe")
        self.eden_mode: bool = False
        self.new_class_mode: bool = False
    
    @staticmethod
    def check_running(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.is_running:
                return method(self, *args, **kwargs)
            else:
                raise pymem.exception.ProcessNotFound("Diva is not running")

        return wrapper
    
    @check_running
    def get_selected_pvid(self) -> int:
        pass