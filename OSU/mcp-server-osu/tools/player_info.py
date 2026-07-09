from fastmcp.tools import tool
from pydantic import BaseModel, Field
from ..osu_get_request import (
    get as request_get,
    Config as RequestConfig
)
import json 
import re
from enum import StrEnum, IntEnum

RE_BEATMAPSET = (
    r'<script id="json-beatmapset" '
    r'type="application/json">(.*?)</script>'
)

class OsuRuleSet(StrEnum):
    osu    = "osu"
    taiko  = "taiko"
    fruits = "fruits"
    mania  = "mania"

class RankStatus(IntEnum):
    graveyard = -2
    wip = -1
    pending = 0
    ranked = 1
    approved = 2
    qualified = 3
    loved = 4

class BeatmapSetInfo(BaseModel):
    beatmapset_id: int = Field(..., description="BeatmapSetID")

    creator: str = Field(..., description="创作者")
    nsfw: bool = Field(..., description="是否包含不良内容")

    bpm: float  = Field(..., description="BPM")
    source: str = Field(..., description="来源")

    title: str  = Field(..., description="歌名（英文）")
    artist: str = Field(..., description="艺术家（英文）")

    title_unicode: str  = Field(..., description="歌名（原名）")
    artist_unicode: str = Field(..., description="艺术家（原名）")

    cover_link: str = Field(..., description="封面链接")

class BeatmapInfo(BeatmapSetInfo):
    beatmap_id: int  = Field(..., description="BeatmapID")
    mode: OsuRuleSet = Field(..., description="游戏模式")

    mapper: str  = Field(..., description="谱面作者")
    version: str = Field(..., description="Beatmap难度名")

    difficulty_rating: float = Field(..., description="难度定数")

    ranked: int   = Field(..., description="谱面rank状态")
    convert: bool = Field(..., description="是否为转换谱面")
    lazer_only: bool = Field(..., description="是否只能在Lazer进行排名")
    
    od: float = Field(..., description="判定严度")
    ar: float = Field(..., description="缩圈速度")
    cs: float = Field(..., description="音符大小")
    hp: float = Field(..., description="掉血速度")

    count_circles: int  = Field(..., description="普通音符总数")
    count_sliders: int  = Field(..., description="滑条音符总数")
    count_spinners: int = Field(..., description="转圈音符总数")


@tool
def get_beatmapset_info(beatmapset_id: int) -> BeatmapSetInfo:
    """
    Description:   
        - 获取osu!谱面集详细信息：标题、艺术家、BPM等
    
    Args:   
        - beatmapset_id (int): 谱面集ID   
    """
    config = RequestConfig()
    status_code, html = request_get(f"beatmapsets/{beatmapset_id}", config)
    match status_code:
        case 200:
            result = re.search(RE_BEATMAPSET, html, re.IGNORECASE | re.DOTALL)
            if not result:
                raise ValueError("该BeatmapSet页面不存在")
        case 404:
            raise Exception(f"该BeatmapSet不存在，请确认beatmapset_id是否正确")
        case _:
            raise Exception(f"无法获取BeatmapSet页面，HTTP {status_code}")
    
    data = json.loads(result.group(1))

    return BeatmapSetInfo(
        beatmapset_id = data["id"],
        creator = data["creator"],

        nsfw = data["nsfw"],
        bpm = data["bpm"],

        source = data["source"],
        
        title = data["title"],
        artist = data["artist"],
        
        artist_unicode = data["artist_unicode"],
        title_unicode = data["title_unicode"],
    )

@tool
def get_beatmap_info(beatmap_id: int) -> BeatmapInfo:
    """
    Description:   
        - 获取osu!谱面详细信息：难度数，模式等
    
    Args:   
        - beatmap_id (int): 谱面ID   
    """
    config = RequestConfig()
    status_code, html = request_get(f"beatmaps/{beatmap_id}", config)
    match status_code:
        case 200:
            result = re.search(RE_BEATMAPSET, html, re.IGNORECASE | re.DOTALL)
            if not result:
                raise ValueError("该Beatmap页面不存在")
        case 404:
            raise Exception(f"该Beatmap不存在，请确认beatmap_id是否正确")
        case _:
            raise Exception(f"无法获取Beatmap页面，HTTP {status_code}")
    
    data = json.loads(result.group(1))

    for beatmap in [*data["beatmaps"], *data["converts"]]:
        if beatmap["id"] == beatmap_id:
            return BeatmapInfo(
                beatmapset_id = data["id"],
                creator = data["creator"],

                nsfw = data["nsfw"],
                bpm = data["bpm"],

                source = data["source"],
                
                title = data["title"],
                artist = data["artist"],
                
                artist_unicode = data["artist_unicode"],
                title_unicode = data["title_unicode"],

                beatmap_id = beatmap["id"],
                mode = beatmap["mode"],

                mapper = beatmap["owners"]["username"],
                version = beatmap["version"],

                difficulty_rating = beatmap["difficulty_rating"],

                ranked = beatmap["ranked"],
                convert = beatmap["convert"],
                lazer_only = beatmap["lazer_only"],

                od = beatmap["accuracy"],
                ar = beatmap["ar"],
                cs = beatmap["cs"],
                hp = beatmap["drain"],

                count_circles = beatmap["count_circles"],
                count_sliders = beatmap["count_sliders"],
                count_spinners = beatmap["count_spinners"],
            )

    raise SystemError("已找到Beatmapset，但没有读取到Beatmap")