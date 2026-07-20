import httpx
import time
from dataclasses import dataclass, asdict
from enum import IntFlag

@dataclass
class ClientConfig:
    client_id:int
    client_secret:str

@dataclass
class TokenConfig:
    token:str = "none"
    token_type:str = "Bearer"
    archive_time:int = -1
    expires_time:int = -1
    
    @property
    def is_active(self) -> bool:
        if self.token == "none" or self.expires_time < 0:
            return False
        else:
            return True
    
    @property
    def is_outdate(self) -> bool:
        if self.is_active == False:
            raise ValueError("Token is not active, cannot check if it is out of date.")

        if (time.time() - self.archive_time) > self.expires_time - 5:
            return True

        return False

    @property
    def head(self) -> dict[str,str]:
        return {"Authorization":f"{self.token_type} {self.token}"}

class OsuModId(IntFlag):
    NF = 1 << 0
    HD = 1 << 3
    HR = 1 << 4
    DT = 1 << 6
    HT = 1 << 8

@dataclass
class BeatmapAttribute:
    bpm:float
    cs:float
    ar:float
    od:float
    hp:float
    hit_length:int
    
    def calc_with_mod(self, mods_int:int) -> 'BeatmapAttribute':
        if mods_int == 0:
            return self
        
        mods: OsuModId = OsuModId(mods_int)
        
        new_data = BeatmapAttribute(**asdict(self))
        
        if OsuModId.HR in mods:
            new_data = BeatmapAttribute(**asdict(self))
            
            new_data.cs = min(10.0, self.cs * 1.3)
            new_data.ar = min(10.0, self.ar * 1.4)
            new_data.od = min(10.0, self.od * 1.4)
            new_data.hp = min(10.0, self.hp * 1.4)
            
        if OsuModId.DT in mods:
            new_data.bpm = self.new_speed_bpm(self.bpm, 1.5)
            new_data.ar  = self.new_speed_ar(self.ar, 1.5)
            new_data.od  = self.new_speed_od(self.od, 1.5)
    
        if OsuModId.HT in mods:
            new_data.bpm = self.new_speed_bpm(self.bpm, 0.75)
            new_data.ar  = self.new_speed_ar(self.ar, 0.75)
            new_data.od  = self.new_speed_od(self.od, 0.75)

        return new_data

    def calc_with_speed(self, speed:float) -> 'BeatmapAttribute':
        return BeatmapAttribute(
            bpm=self.new_speed_bpm(self.bpm, speed),
            cs=self.cs,
            ar=self.new_speed_ar(self.ar, speed),
            od=self.new_speed_od(self.od, speed),
            hp=self.hp,
            hit_length=int(self.hit_length / speed)
        )

    @staticmethod
    def new_speed_ar(original_ar:float, speed:float) -> float:
        if original_ar <= 5.0:
            preempt = 1800 - 120 * original_ar
        else:
            preempt = 1200 - 150 * (original_ar - 5)
        
        new_preempt = preempt / speed
        
        if new_preempt > 1200:
            new_ar = (1800 - new_preempt) / 120
        else:
            new_ar = 5 + (1200 - new_preempt) / 150
        
        return new_ar
    
    @staticmethod
    def new_speed_od(original_od:float, speed:float) -> float:
        hit_window = 80 - 6 * original_od
        new_hit_window = hit_window / speed
        
        new_od = (80 - new_hit_window) / 6
        
        return new_od
    
    @staticmethod
    def new_speed_bpm(original_bpm:float, speed:float) -> float:
        return original_bpm * speed

@dataclass
class BeatmapInfo:
    id:int
    url:str
    difficulty_rating:float
    
    version:str
    cover_url:str
    
    title:str
    title_unicode:str
    
    artist:str
    artist_unicode:str
    
    attribute:BeatmapAttribute
    
    @property
    def dict_data(self) -> dict:
        data = asdict(self)
        attribute_data = data.pop("attribute")
        data.update(attribute_data)

        return data
        

class OsuApiV2:
    TOKEN_URL = r"https://osu.ppy.sh/oauth/token"
    APIV2_URL = r"https://osu.ppy.sh/api/v2"

    def __init__(self, client_config:ClientConfig) -> None:
        
        self.client_id:int = client_config.client_id
        self.client_secret:str = client_config.client_secret
        
        self.token: TokenConfig = TokenConfig()
        self.archive_token()

    def check_token(self) -> bool:
        """
        检测token
        """
        if self.token.is_outdate:
            return self.refresh_token()
        else:
            return True
        
    def session_post(self,session:httpx.Client, url:str, json_data:dict|None = None) -> dict:
        response = session.post(url, json=json_data)
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return {}
    
    def session_get(self,session:httpx.Client, url:str, params:dict|None = None) -> dict:
        response = session.get(url, params=params)
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return {}
        
    def archive_token(self) -> bool:
        """
        获取token  
        直接赋值给self变量，使用初始值检测的方式确认是否数据有误
        """
        client_data:dict = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "public"
            }
        try:
            with httpx.Client() as session:
                token_data = self.session_post(session, OsuApiV2.TOKEN_URL, client_data)
                if not token_data:
                    return False
                
                self.token = TokenConfig(
                    token_data["access_token"],
                    token_data["token_type"],
                    int(time.time()),
                    token_data["expires_in"],
                )

                return True

        except Exception:
            #如果无法获取就赋值初始值
            self.token = TokenConfig()

        return False
    
    def refresh_token(self) -> bool:
        """
        刷新token  
        直接赋值给self变量，使用初始值检测的方式确认是否数据有误
        """
        client_data:dict = {
            "client_id"    : self.client_id,
            "client_secret": self.client_secret,
            "grant_type"   : "refresh_token",
            "refresh_token": self.token
            }
        try:
            with httpx.Client() as session:
                token_data = self.session_post(session, OsuApiV2.TOKEN_URL, client_data)
                if not token_data:
                    return False
                
                self.token = TokenConfig(
                    token_data["access_token"],
                    token_data["token_type"],
                    int(time.time()),
                    token_data["expires_in"],
                )
                
                return True
            
        except Exception:
            #如果无法获取就赋值初始值
            self.token = TokenConfig()

        return False
    
    def get(self, api_suffix:str, params:dict|None = None) -> dict:
        if self.check_token():
            with httpx.Client(headers=self.token.head) as session:
                return self.session_get(session, f"{OsuApiV2.APIV2_URL}/{api_suffix}", params)
        else:
            return {}
    
    def post(self, api_suffix:str, json_data:dict|None = None) -> dict:
        if self.check_token():
            with httpx.Client(headers=self.token.head) as session:
                return self.session_post(session, f"{OsuApiV2.APIV2_URL}/{api_suffix}", json_data)
        else:
            return {}



def get_beatmap_info(v2_api:OsuApiV2, bid:int, use_mods:OsuModId= OsuModId.NF) -> dict[str,str]|None:
    beatmap_info:dict = v2_api.get(f"beatmaps/{bid}")
    attributes:dict = v2_api.post(f"beatmaps/{bid}/attributes", json_data={"mods": int(use_mods)})
    
    beatmap_data: BeatmapInfo = BeatmapInfo(
        id  = beatmap_info["id"],
        url = beatmap_info["url"],
        
        difficulty_rating = attributes["attributes"]["star_rating"],
        version           = beatmap_info["version"],
        cover_url         = beatmap_info["beatmapset"]["covers"]["cover"],
        
        title          = beatmap_info["beatmapset"]["title"],
        title_unicode  = beatmap_info["beatmapset"]["title_unicode"],
        artist         = beatmap_info["beatmapset"]["artist"],
        artist_unicode = beatmap_info["beatmapset"]["artist_unicode"],
        
        attribute=BeatmapAttribute(
            bpm = beatmap_info["bpm"],
            cs  = beatmap_info["cs"],
            ar  = beatmap_info["ar"],
            od  = beatmap_info["accuracy"],
            hp  = beatmap_info["drain"],
            hit_length = beatmap_info["hit_length"]
        ).calc_with_mod(use_mods)
    )
    
    return beatmap_data.dict_data


if __name__ == "__main__":
    client_config = ClientConfig(
        client_id= -1,
        client_secret="Get your own client_id and client_secret from https://osu.ppy.sh/home/account/edit"
    )
    osu_api = OsuApiV2(client_config)
    from pprint import pprint
    print("NM")
    pprint(get_beatmap_info(osu_api, 5265618))
    print("HR+DT")
    pprint(get_beatmap_info(osu_api, 5265618, OsuModId.HR | OsuModId.DT))