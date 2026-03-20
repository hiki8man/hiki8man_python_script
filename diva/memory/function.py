from manager import DivaMemoryManager
from address import DivaAddress, NewClassicsAddress
from model import *
import pymem.exception

@DivaMemoryManager.check_running
def get_rom_folder_list(manager:DivaMemoryManager) -> list[str]:
    import ctypes
    string_list = []
    start_address = DivaAddress.DBFolderInfo.first.get_address(manager)
    end_address = DivaAddress.DBFolderInfo.last.get_address(manager)

    currect_address: int = start_address
    count = abs(end_address - start_address) // ctypes.sizeof(DivaString)
    
    for _ in range(count):
        string_list.append(manager.read_diva_string(currect_address))
        currect_address += ctypes.sizeof(DivaString)
    
    return string_list    

@DivaMemoryManager.check_running
def get_pvid_list(manager:DivaMemoryManager) -> list[int]:
    start_address = DivaAddress.DBInfo.first.get_address(manager)
    end_address = DivaAddress.DBInfo.last.get_address(manager)
    
    pvid_list: list = []
    currect_address: int = start_address
    count = abs(end_address - start_address) // 8
    
    for _ in range(count):
        pvdb_address = manager.read_ulonglong(currect_address)
        pv_id = manager.read_uint(pvdb_address)
        pvid_list.append(pv_id)
        currect_address += 8
    
    return pvid_list    

@DivaMemoryManager.check_running
def get_selected_song(manager:DivaMemoryManager) -> int:
    # 0表示非选歌界面
    # -1表示错误状态
    # -2表示选中随机打歌
    # 其他表示当前ID
    random_address: int = DivaAddress.GetSelectSong.random.get_address(manager)
    select_address: int = DivaAddress.GetSelectSong.selected.get_address(manager)

    if random_address > 0:
        selected_pvid = manager.read_int(random_address)

    elif select_address > 0:
        selected_pvid = manager.read_int(select_address)

    else:
        selected_pvid = -1

    return selected_pvid if isinstance(selected_pvid, int) else -1

@DivaMemoryManager.check_running
def get_new_class_mode(manager:DivaMemoryManager) -> int:
    currect_mode_address = NewClassicsAddress.Mode.state.get_address(manager)
    try:
        if currect_mode_address:
            currect_mode = manager.read_int(currect_mode_address)
            return currect_mode if isinstance(currect_mode, int) else NewClassicsStyle.ARCADE
        else:
            return NewClassicsStyle.ARCADE
    except pymem.exception.MemoryReadError|pymem.exception.ProcessNotFound:
        return NewClassicsStyle.ARCADE

@DivaMemoryManager.check_running
def get_db_loader_log(manager:DivaMemoryManager) -> str:
    address = DivaAddress.DBLogger.address.get_address(manager)
    if not address:
        return ""

    db_log = manager.read_cstring(address)
    return db_log if isinstance(db_log, str) else ""

if __name__ == "__main__":
    a = DivaMemoryManager()
    print(get_rom_folder_list(a))
    print(get_pvid_list(a))
    print(len(get_pvid_list(a)))
    print(NewClassicsStyle(get_new_class_mode(a)).name)
    print(get_db_loader_log(a))
    while True:
        print(NewClassicsStyle(get_new_class_mode(a)).name)