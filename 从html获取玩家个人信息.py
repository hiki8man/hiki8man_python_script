import httpx
import re, json

GAME_MODE = ("osu","taiko","fruits","mania")

RE_USER_INFO = r'data-initial-data="(.*)"'

def convert_time(time:int) -> str:
    time_m, time_s = divmod(time, 60)
    time_h, time_m = divmod(time_m, 60)
    return f"{time_h} 小时 {time_m} 分钟 {time_s} 秒"

def get_user_info(user_id:int|str, mode:int=-1) -> dict:
    if isinstance(user_id,int) or user_id == "me":
        with httpx.Client(base_url="https://osu.ppy.sh/users/",verify=False) as USER_CLIENT:
            response = USER_CLIENT.get(f"{user_id}/{GAME_MODE[mode] if mode > -1 and mode < 4 else ""}")
            if response.status_code == 200:
                html_text = response.text
                json_text = re.search(RE_USER_INFO,html_text).group(1).replace("&quot;",'"')
                user_data = json.loads(json_text)["user"]

                return {"username"    :user_data["username"],
                        "playmode"    :user_data["playmode"],
                        "pp"          :user_data["statistics"]["pp"],
                        "global_rank" :user_data["statistics"]["global_rank"],
                        "country"     :user_data["country"]["name"],
                        "country_rank":user_data["statistics"]["country_rank"],
                        "ranked_score":user_data["statistics"]["ranked_score"],
                        "hit_accuracy":user_data["statistics"]["hit_accuracy"],
                        "play_count"  :user_data["statistics"]["play_count"],
                        "total_hits"  :user_data["statistics"]["total_hits"],
                        "play_time"   :user_data["statistics"]["play_time"],
                        "is_ranked"   :user_data["statistics"]["is_ranked"]}
    
    return {}

# 仿消防栓获取玩家信息
if __name__ == "__main__":
    info:dict = get_user_info(2)
    if info:
        print(f'''{info["username"]}的个人信息-{info["playmode"]}

{info["pp"]}pp 表现
#{info["global_rank"]}
{info["country"]} #{info["country_rank"]}
{info["ranked_score"]} Ranked谱面总分
{info["hit_accuracy"]}% 准确率
{info["total_hits"]} 总命中次数
{convert_time(info["play_time"])}游玩时间{"" if info["is_ranked"] else "\n用户不活跃"}
''')