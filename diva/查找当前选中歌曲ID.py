import pymem
from collections.abc import Generator
import psutil
from pathlib import Path

def get_game_pymem() -> pymem.Pymem:
    try:
        return pymem.Pymem('DivaMegaMix.exe')
    except pymem.exception.ProcessNotFound:
        raise OSError("游戏进程不存在")

def get_select_pvid() -> int:
    '''
    返回 0 代表没有选中歌曲
    否则返回pvid
    '''
    currect_pvid_base_address = game_pymem.read_int(game_address + int("0xCC5EF18" , 16))
    if currect_pvid_base_address == 0 or not isinstance(currect_pvid_base_address, int):
        # 尝试获取打歌界面pvid
        # 打歌界面pvid空值为0xFFFFFFFF
        currect_pvid = game_pymem.read_uint(game_address + int("0x16E2BB0" , 16))
    else:
        # 选歌界面pvid空值为0xFFFFFFFE
        pvid_address = currect_pvid_base_address + int("0x000258DC", 16)
        currect_pvid = game_pymem.read_uint(pvid_address)

    if currect_pvid in (int("0xFFFFFFFF", 16),int("0xFFFFFFFE", 16)) or not isinstance(currect_pvid, int):
        return 0
    else:
        return currect_pvid

if __name__ == "__main__":
    # 测试用，实时输出pvid
    game_pymem = get_game_pymem()
    game_address = game_pymem.base_address
    while True:
        print(get_select_pvid())
