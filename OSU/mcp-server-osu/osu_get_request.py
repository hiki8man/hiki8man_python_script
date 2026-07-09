import httpx
from httpx_curl_cffi import CurlTransport
from dataclasses import dataclass

@dataclass
class Config:
    from httpx._types import (
        ProxyTypes, QueryParamTypes, 
        CookieTypes, URL
    )

    base_url: URL|str = "https://osu.ppy.sh/"
    timeout: int = 10
    impersonate: str = "firefox"
    proxies: ProxyTypes = None
    follow_redirects: bool = True
    params: QueryParamTypes|None = None
    cookies: CookieTypes|None = None
    verify: bool = True
    @property
    def transport(self) -> CurlTransport:
        return CurlTransport(impersonate=self.impersonate)
    
    def get_params(self) -> dict:
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "transport": self.transport,
            "proxies": self.proxies,
            "follow_redirects": self.follow_redirects,
            "params": self.params,
            "cookies": self.cookies,
            "verify": self.verify,
        }

def get(url: str, config: Config=Config()) -> tuple[int,str]:
    with httpx.Client(**config.get_params()) as client:
        response = client.get(url)
        response.raise_for_status()
        return (response.status_code, response.text)

async def get_async(url: str, config: Config=Config()) -> tuple[int,str]:
    async with httpx.AsyncClient(**config.get_params()) as client:
        response = client.get(url)
        response.raise_for_status()
        return (response.status_code, response.text)
