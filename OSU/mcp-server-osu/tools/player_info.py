from fastmcp.tools import tool
from fastmcp.prompts import prompt
from enum import StrEnum
from pydantic import BaseModel, Field

class MapType(StrEnum):
    BEATMAP = "beatmap"
    BEATMAPSET = "beatmapset"

class BeatmapSetInfo(BaseModel):
    title: str  = Field(..., description="歌名（英文）")
    title_unicode:str = Field(..., description="歌名")
    artist: str = Field(..., description="艺术家（英文）")
    artist_unicode:str = Field(..., description="艺术家")
    bpm: float  = Field(..., description="BPM")
    creator: str = Field(..., description="谱师")
    source: str = Field(..., description="来源")

class BeatmapInfo(BeatmapSetInfo):
    beatmap_id: str = Field(..., description="单谱面ID")

@tool
def get_beatmap_info(map_id: int) -> BeatmapInfo:
    """
    Description:   
        - 获取osu!谱面集详细信息：标题、艺术家、BPM、难度参数等

    Args:
        - map_type (MapType): 查询类型，可选 "beatmap"（单谱面）或 "beatmapset"（谱面集）   
        - map_id (int): 谱面ID
    """

@tool
def get_beatsetmap_info(map_id: int) -> BeatmapSetInfo:
    """
    Description:   
        - 获取osu!谱面详细信息：标题、艺术家、BPM、难度参数等

    Args:
        - map_id (int): 谱面ID
    """
