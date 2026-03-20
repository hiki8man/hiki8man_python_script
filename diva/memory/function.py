from manager import DivaMemoryManager
from address import DivaAddress, NewClassicsAddress
from model import *
import pymem.exception
import time

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
    except PYMEM_ERRORS:
        return NewClassicsStyle.ARCADE

@DivaMemoryManager.check_running
def switch_new_class_mode(manager:DivaMemoryManager, mode:NewClassicsStyle) -> bool:
    if manager.check_new_classics == False:
        return False
    
    currect_mode_address = NewClassicsAddress.Mode.state.get_address(manager)
    try:
        if currect_mode_address:
            manager.write_int(currect_mode_address, mode.value)
            return True
        else:
            return False

    except PYMEM_ERRORS:
        return False

@DivaMemoryManager.check_running
def switch_song(manager:DivaMemoryManager, song:SwitchSong) -> int:
    def change_last_select(manager:DivaMemoryManager, song:SwitchSong) -> None:
        try:
            last_pvid_address = DivaAddress.LastSelect.pvid.get_address(manager)
            last_sort_address = DivaAddress.LastSelect.sort.get_address(manager)
            last_diff_type_address = DivaAddress.LastSelect.diff_type.get_address(manager)
            last_diff_value_address = DivaAddress.LastSelect.diff_value.get_address(manager)

            if manager.check_eden:
                last_pvid_address += DivaAddress.Offset.eden
                last_sort_address += DivaAddress.Offset.eden
                last_diff_type_address += DivaAddress.Offset.eden
                last_diff_value_address += DivaAddress.Offset.eden

            manager.write_int(last_pvid_address, song.pvid)
            manager.write_int(last_sort_address, 1) # diff排序
            manager.write_int(last_diff_type_address, song.difficulty)
            manager.write_int(last_diff_value_address, 19) # all
            switch_new_class_mode(manager, song.style)
        except PYMEM_ERRORS:
            pass

    try:
        state_address = DivaAddress.GameState.next.get_address(manager)
        change_address = DivaAddress.GameState.change.get_address(manager)
        pvid_list = get_pvid_list(manager)
        if song.pvid in pvid_list:
            if manager.read_int(state_address) == 6:
                # 跳到pv鉴赏
                manager.write_int(state_address, 6)
                manager.write_int(change_address, 2)
                time.sleep(0.1) # 堵塞等待diva跳转
                # 执行操作
                change_last_select(manager, song)
                # 跳转选歌界面
                manager.write_int(state_address, 5)
                manager.write_int(change_address, 2)
            else:
                change_last_select(manager, song)
            return song.pvid

        else:
            return 0

    except PYMEM_ERRORS:
        return 0

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