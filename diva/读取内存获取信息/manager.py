import pymem
import pymem.exception
import pymem.process
import psutil

from functools import wraps
from model import DivaString
from address import DivaAddress

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
    def __init__(self) -> None:
        super().__init__("DivaMegaMix.exe")
    
    @property
    def check_eden(self) -> bool:
        value = self.read_uint(DivaAddress.LastSelect.sort.get_address(self))
        return True if not value else False
    
    @property
    def check_new_classics(self) -> bool:
        for module in self.list_modules():
            if module == "NewClassics.dll": return True
        return False
    
    def reboot(self) -> None:
        self.open_program()

    @staticmethod
    def check_running(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.is_running:
                return method(self, *args, **kwargs)

            self.reboot()
            if self.is_running:
                return method(self, *args, **kwargs)

            raise pymem.exception.ProcessNotFound("Diva is not running")

        return wrapper
    
    def read_diva_string(self, address: int) -> str:
        import struct
        string_info = self.read_ctype(address, DivaString())
        if not isinstance(string_info, DivaString):
            return ""
        
        data_byte = bytes(string_info.data_byte)
        if string_info.data_size > 15:
            string_address = struct.unpack("<Q",data_byte[:8])[0]
            string = self.read_cstring(string_address)
        else:
            string = data_byte[:string_info.end_point].decode("utf-8")
        
        return string

