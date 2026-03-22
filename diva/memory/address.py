from dataclasses import dataclass
from memory_utils import Address, Pointer, DynamicOffset32, DynamicOffset64, StaticOffset32, StaticOffset64, PatternScan, PatternSrting


@dataclass(frozen=True)
class DivaAddress:
    class Offset:
        eden: int = 0x105F460 # 影响LastSelect
    
    class LastSelect:
        diff_type: Address = Address(0x12B634C)
        pvid: Address = Address(0x12B6350)
        sort: Address = Address(0x12B6354)
        '''
        value按顺序从0开始自增，其中all和喜爱一定是最后两个数
        难度比较特殊，其按照所有难度排序计数，再添加末尾值
        '''
        name_value: Address = Address(0x12B6358)
        diff_value: Address = Address(0x12B635C)
        chara_value: Address = Address(0x12B6360)
        score_value: Address = Address(0x12B6364)
    
    class GameState:
        unknow: Address = Address(0xCC61090) # 不明
        current: Address = Address(0xCC61094) # 当前state
        next_jump: Address = Address(0xCC61098) # 即将跳转到state
        before: Address = Address(0xCC6109C) # 上次的state
        archive: Address = Address(0xCC610A0) #其为二进制，01表示已完成，11表示准备跳转

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
    
    class GetSelectDifficulty:
        pattern: PatternSrting = PatternSrting(
            br"\x48\x89\x5C\x24\x08"
            br"\x48\x89\x6C\x24\x10"
            br"\x48\x89\x74\x24\x18"
            br"\x57"
            br"\x48\x83\xEC\x20"
            br"\x33\xED"
            br"\x48\xC7\x41\x20\xFF\xFF\xFF\xFF",
            offset=-16, lenght=7
        )
        #type: Address = Address(0x16E2B90)
        #is_ex: Address = Address(0x16E2B94)
        type: Address = Address(PatternScan(pattern))
        is_ex: Address = Address(PatternScan(pattern, 4))

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
        pattern: PatternSrting = PatternSrting(
            br"\x74\x0B"
            br"\x8B\x88...."
            br"\x83\xF9\x03"
            br"\x75\x02"
            br"\x33\xC9"
            br"\x89\x0D...."
            br"\x40\x0F\xB6\xC7"
            br"\x48\x8B\xC4\x30",
            offset=15, lenght=6
        )
        state: Address = Address(PatternScan(pattern), "NewClassics.dll")