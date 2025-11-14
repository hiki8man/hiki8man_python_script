import httpx
import re,json
RE_BEATMAPSET = r'<script id="json-beatmapset" type="application/json">\n        (.*?)\n    </script>'

def get_response(url:str) -> tuple[str, str]:
    response = httpx.get(url,follow_redirects=True,verify=False)
    if response.status_code == 200:
        return (str(response.url), response.text)
    else:
        raise ValueError("无法获取信息")

def get_info_osu_html(mapid_type:str, mapid_num:int) -> dict[str,str|int|bool]|None:
    '''
    解析谱面页面获取谱面信息  
    [TODO] 优化传出的数据结构格式
    '''
    map_url, html_text =  get_response(f"https://osu.ppy.sh/{mapid_type}/{mapid_num}")
    # 更换mapid类型尝试二次搜索
    if not map_url:
        mapid_type = "s" if mapid_type == "b" else "b"
        map_url, html_text = get_response(f"https://osu.ppy.sh/{mapid_type}/{mapid_num}")
    
    if map_url:
        # 从网页获取谱面信息
        match = re.search(RE_BEATMAPSET, html_text, re.IGNORECASE)
        if match:
            json_data = json.loads(match.group(1))
            result =  {"artist"        :json_data["artist"],
                       "artist_unicode":json_data["artist_unicode"],
                       "title"         :json_data["title"],
                       "title_unicode" :json_data["title_unicode"],
                       "sid"           :json_data["id"],
                       "map_url"       :map_url,
                       "bpm"           :json_data["bpm"],
                       "cover_img_url" :json_data["covers"]["cover@2x"],
                       "list_img_url"  :json_data["covers"]["list@2x"],
                       "card_img_url"  :json_data["covers"]["card@2x"],
                       "ranked"        :json_data["ranked"],
                       "is_beatmap"    :mapid_type == "b",
                       "nsfw"          :json_data["nsfw"],
                       "offset"        :json_data["offset"]
                       }
            
            if mapid_type == "b":
                for beatmap in json_data["beatmaps"]:
                    if beatmap["id"] == mapid_num:
                        result.update({"bid"           :beatmap["id"],
                                       "mode"          :beatmap["mode"],
                                       "diff_name"     :beatmap["version"],
                                       "od"            :beatmap["accuracy"],
                                       "ar"            :beatmap["ar"],
                                       "hp"            :beatmap["drain"],
                                       "cs"            :beatmap["cs"],
                                       "diff_rating"   :beatmap["difficulty_rating"],
                                       "bpm"           :beatmap["bpm"],
                                       "song_length"   :beatmap["total_length"],
                                       "chart_lenght"  :beatmap["hit_length"],
                                       "max_combo"     :beatmap["max_combo"],
                                       "count_circles" :beatmap["count_circles"],
                                       "count_sliders" :beatmap["count_sliders"],
                                       "count_spinners":beatmap["count_spinners"],
                                       })
                        return result


if __name__ == "__main__":
    info_dict = get_info_osu_html("b",2039171)
    if not info_dict:
        raise ValueError("无法获取谱面信息")
    print(f"{info_dict["title_unicode"]}: {info_dict["map_url"]}")