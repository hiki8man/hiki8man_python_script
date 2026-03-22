from manager import DivaMemoryManager
from address import DivaAddress, NewClassicsAddress
from model import *
import pymem.exception
import time

PYMEM_ERRORS = (pymem.exception.MemoryWriteError, 
                pymem.exception.MemoryReadError,
                pymem.exception.ProcessNotFound)

@DivaMemoryManager.check_running
def get_rom_folder_list(manager:DivaMemoryManager) -> list[str]:
    '''
    返回当前加载的所有mod的rom路径   
    注意其也会读取cpk的路径，可以用来判断是否有dlc
    '''
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
    '''
    返回可用的pvid列表，理论上可以做完整解析获取对应难度，感觉没必要
    '''
    
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
def get_selected_difficulty(manager: DivaMemoryManager) -> int:
    # -2表示错误状态
    # -1表示难度不存在
    # 其他表示难度
    try:
        type_address = DivaAddress.GetSelectDifficulty.type.get_address(manager)
        flag_address = DivaAddress.GetSelectDifficulty.is_ex.get_address(manager)
        
        type = manager.read_int(type_address)
        flag = manager.read_bool(flag_address)

        if not isinstance(type, int) or not isinstance(flag, bool):
            return -2
        
        selected_difficulty = StoredDifficulty.get_selected_difficulty(type, flag)
        return selected_difficulty

    except PYMEM_ERRORS:
        return -2
    except ValueError:
        return -1

@DivaMemoryManager.check_running
def get_new_class_mode(manager:DivaMemoryManager) -> int:
    '''
    返回谱面风格，如果错误则返回ARCADE
    '''
    
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
    '''
    返回是否执行成功
    '''
    
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
def get_currect_state(manager: DivaMemoryManager) -> int:
    '''
    返回游戏状态
    -1 表示内存操作失败
    0 表示无法读取
    其他值对应不同状态
    '''
    
    current_address = DivaAddress.GameState.current.get_address(manager)
    try:
        state_value = manager.read_int(current_address)
        if isinstance(state_value, int):
            return state_value
        else:
            return 0

    except PYMEM_ERRORS:
        return -1

@DivaMemoryManager.check_running
def get_now_playing(manager: DivaMemoryManager) -> int:
    '''
    当前游玩的歌曲  
    内存操作失败返回 -1
    不在游玩界面返回 0
    其他整数返回 pvid
    '''
    if get_currect_state(manager) != GameState.PLAYING:
        return 0
    
    now_playing_address = DivaAddress.GetSelectSong.playing.get_address(manager)
    try:
        now_palying_value = manager.read_int(now_playing_address)
        if isinstance(now_palying_value, int):
            return now_palying_value
        else:
            return -1

    except PYMEM_ERRORS:
        return -1
        

@DivaMemoryManager.check_running
def switch_song(manager:DivaMemoryManager, song:SwitchSong) -> int:
    '''
    跳转歌曲
    -1表示内存操作失败
    0表示没有找到歌
    其他正数表示pvid
    '''
    def change_last_select(manager:DivaMemoryManager, song:SwitchSong) -> None:
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
        manager.write_int(last_sort_address, SelectSort.by_difficulty) # diff排序
        manager.write_int(last_diff_type_address, song.difficulty)
        manager.write_int(last_diff_value_address, 19) # all
        switch_new_class_mode(manager, song.style)

    def change_state(manager: DivaMemoryManager, state: GameState) -> None:
        next_state_address = DivaAddress.GameState.next_jump.get_address(manager)
        archive_address = DivaAddress.GameState.archive.get_address(manager)
        manager.write_int(next_state_address, state)
        manager.write_int(archive_address, ArchiveChange.START)
    
    try:
        pvid_list = get_pvid_list(manager)
        if not song.pvid in pvid_list:
            return 0

        if get_currect_state(manager) == GameState.SELECT:
            change_state(manager, GameState.WATCH) # 跳到pv鉴赏
            time.sleep(0.1) # 堵塞等待diva跳转
            change_last_select(manager, song) # 执行操作
            change_state(manager, GameState.SELECT) # 跳转选歌界面
        else:
            change_last_select(manager, song) # 执行操作

        return song.pvid

    except PYMEM_ERRORS:
        return -1

@DivaMemoryManager.check_running
def get_db_loader_log(manager:DivaMemoryManager) -> str:
    '''
    返回db loader日志
    '''
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
    print(GameState(get_currect_state(a)).name)
    # print(switch_song(a, SwitchSong(722, Difficulty.EASY, NewClassicsStyle.ARCADE)))
    print(get_now_playing(a))
    while True:
        print(StoredDifficulty(get_selected_difficulty(a)).name)
 