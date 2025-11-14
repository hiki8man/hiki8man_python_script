import httpx
import re
USER_CLIENT = httpx.Client(base_url="https://osu.ppy.sh/users/")

def get_bonus_pp(user_id:int):
    response = USER_CLIENT.get(f"{user_id}/extra-pages/historical",params={"mode":"osu"})
    data = response.json()
    N = data["beatmap_playcounts"]["count"]
    return (417.0 - 1.0/3.0) * (1.0 - pow(0.995, min(N, 1000)))

def get_bp_count(user_id:int):
    response = USER_CLIENT.get(f"{user_id}/extra-pages/top_ranks",params={"mode":"osu"})
    data = response.json()
    return data["best"]["count"]

def get_bp_list(user_id:int):
    best_count = get_bp_count(user_id)
    bp_list = USER_CLIENT.get(f"{user_id}/scores/best",params={"mode":"osu","offset":0,"limit":100}).json()
    if best_count > 100:
        bp_list += USER_CLIENT.get(f"{user_id}/scores/best",params={"mode":"osu","offset":100,"limit":100}).json()
    
    return bp_list

def get_pp_bplist(user_id:int):
    # 根据BP列表获取总PP值
    # 不准确，原因不明，已确认bonus pp计算公式没有问题
    pp_value = 0
    bp_list = get_bp_list(user_id)

    for bp in bp_list:
        pp_value += bp["weight"]["pp"]
    bouns_pp = get_bonus_pp(user_id)
    pp_value += bouns_pp
    pass

def get_acc_bplist(user_id:int):
    # 根据BP列表获取准确度值
    acc_value = 0.0
    bp_list = get_bp_list(user_id)
    for bp in bp_list:
        acc_value += bp["accuracy"] * bp["weight"]["percentage"]
    acc_value *= (100 / (20 * (1 - 0.95 ** len(bp_list))))
    acc_value = round(acc_value) / 100
    pass
