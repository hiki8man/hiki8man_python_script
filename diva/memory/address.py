from dataclasses import dataclass
from .memory_utils import Address, Pointer, DynamicOffset32, DynamicOffset64, StaticOffset32, StaticOffset64, PatternScan


@dataclass(frozen=True)
class DivaAddress:
    class Offset:
        eden: int = 0x105F460 # 影响LastSelect
    
    class LastSelect:
        pvid: Address = Address(0x12B6350)
        sort: Address = Address(0x12B6354)
        diff_type: Address = Address(0x12B634C)
        diff_value: Address = Address(0x12B635C)
    
    class GameState:
        next: Address = Address(0xCC61098) # 6表示pv鉴赏模式，2表示选歌界面
        change: Address = Address(0xCC610A0) #其为二进制，01表示已完成，11表示准备跳转

    class GetSelectSong:
        playing: Address = Address(0x16E2BB0)
        # 主用方案，需要根据是否为随机获取值，但随机值获取指针有点奇怪
        selected: Address = Address(
            Pointer(
                0xCC5EF18, 
                [DynamicOffset32(0x6EFE8C)], 
            )
        )
        random: Address= Address(
            Pointer(
                0xCBFA9C0, 
                [DynamicOffset32(0x6EFE8A), StaticOffset32(0), StaticOffset32(0)]
            )
        )
        # 备用方案，是不是随机都可以都在这里读，但是定位方法比较奇怪
        selected_with_random: Address = Address(
            Pointer(
                0xCC5EF18, 
                [DynamicOffset32(0x6EFE8C)], 
                -0x9c8
            )
        )
        
    class DBInfo:
        first: Address = Address(Pointer(0x1753818))
        last: Address = Address(Pointer(0x1753820))
        capacity_end: Address = Address(Pointer(0x1753828)) # 给出多余空间便于后续添加
        
    class DBFolderInfo:
        first: Address = Address(Pointer(0x14AB8A0))
        last: Address = Address(Pointer(0x14AB8A8))
        capacity_end: Address = Address(Pointer(0x14AB8B0)) # 给出多余空间便于后续添加
        
    class DBLogger:
        address: Address = Address(Pointer(0x16EBDD0))

@dataclass(frozen=True)
class NewClassicsAddress:
    class Mode:
        pattern: bytes = b"\x74\x0B\x8B\x88....\x83\xF9\x03\x75\x02\x33\xC9\x89\x0D....\x40\x0F\xB6\xC7\x48\x8B"
        state: Address = Address(PatternScan(pattern, 17), "NewClassics.dll")