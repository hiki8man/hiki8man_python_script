import pymem
import pymem.exception
import psutil
from functools import wraps
from model import *

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
    def eden_mode(self) -> bool:
        value = self.read_uint(DivaAddress.LastSelect.sort)
        return True if value else False
    
    @property
    def new_class_address(self) -> int:
        for module in self.list_modules():
            if module.name == "NewClassics.dll":
                return module.lpBaseOfDll
        return 0   
    
    @staticmethod
    def check_running(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.is_running:
                return method(self, *args, **kwargs)
            else:
                # 尝试重新加载
                self.open_program()
                if self.is_running == False:
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


@DivaMemoryManager.check_running
def get_string_list(self, start_address: int, end_address: int) -> list[str]:
    import ctypes
    string_list = []
    currect_address: int = start_address
    count = abs(end_address - start_address) // ctypes.sizeof(DivaString)
    
    for _ in range(count):
        string_list.append(self.read_diva_string(currect_address))
        currect_address += ctypes.sizeof(DivaString)
    
    return string_list    

@DivaMemoryManager.check_running
def get_pvid_list(manager:DivaMemoryManager) -> list[int]:
    start_address = DivaAddress.DBInfo.first.calculate_address(manager)
    end_address = DivaAddress.DBInfo.last.calculate_address(manager)
    
    pvid_list: list = []
    currect_address: int = start_address
    count = abs(end_address - start_address) // 8
    
    for _ in range(count):
        pvdb_address = manager.read_ulonglong(currect_address)
        pv_id = manager.read_uint(pvdb_address)
        pvid_list.append(pv_id)
        if pv_id == 72:
            pass
        currect_address += 8
    
    return pvid_list    

@DivaMemoryManager.check_running
def get_selected_song(manager:DivaMemoryManager) -> int:
    # 0表示非选歌界面
    # -1表示错误状态
    # -2表示选中随机打歌
    # 其他表示当前ID
    random_address = DivaAddress.GetSelectSong.random.calculate_address(manager)
    select_address = DivaAddress.GetSelectSong.selected.calculate_address(manager)

    if isinstance(random_address, int) and random_address >0:
        selected_pvid = manager.read_int(random_address)
        assert isinstance(selected_pvid, int)
    elif isinstance(select_address, int) and select_address >0:
        selected_pvid = manager.read_int(select_address)
        assert isinstance(selected_pvid, int)
    else:
        selected_pvid = -1
    return selected_pvid

@DivaMemoryManager.check_running
def get_new_class_mode(manager:DivaMemoryManager) -> int:
    base_address = manager.new_class_address
    if base_address:
        currect_mode_address = NewClassicsAddress.Mode.state.calculate_address(manager, base_address)
        currect_mode = manager.read_int(currect_mode_address)
        return currect_mode if isinstance(currect_mode, int) else NewClassicsStyle.ARCADE
    else:
        return NewClassicsStyle.ARCADE

if __name__ == "__main__":
    a = DivaMemoryManager()
    start_address = DivaAddress.DBFolderInfo.first.calculate_address(a)
    end_address = DivaAddress.DBFolderInfo.last.calculate_address(a)
    print(get_pvid_list(a))
    print(len(get_pvid_list(a)))
    print(NewClassicsStyle(get_new_class_mode(a)).name)
    while True:
        pvid = get_selected_song(a)
        print(f"{SelectState(get_selected_song(a)).name}:{pvid if pvid > 0 else ""}")
