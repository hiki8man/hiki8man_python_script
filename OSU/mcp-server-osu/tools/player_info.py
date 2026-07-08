from fastmcp.tools import tool
from enum import StrEnum
from pydantic import BaseModel

class MapType(StrEnum):
    BEATMAP    = "b"
    BEATMAPSET = "s"

@tool
def get_beatmap_info(map_type: MapType, map_id: int) -> dict:
    """
    Description:   
        - 获取osu!谱面详细信息：标题、艺术家、BPM、难度参数等

    Args:
        - map_type (MapType): 查询类型，可选 "beatmap"（单谱面）或 "beatmapset"（谱面集）   
        - map_id (int): 谱面ID
    """