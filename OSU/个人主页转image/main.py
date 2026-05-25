import plutoprint
import io
import httpx
import json
import re
import html
from pathlib import Path
from PIL import Image
import time

GET_USER_JSON: re.Pattern = re.compile(r'data-initial-data="(.*)"\s+data-react="profile-page"')
WEBP_MAX: int = 8000 # 最大是16383，但QQ有大小限制10mb，保险起见削弱一下
MAX_HEIGHT: int = 30000 # QQ有最大像素限制，暂时限定死3w
QQ_PNG_SIZE_MAX: int = 1024 * 1024 # 10mb


class DataFeather(plutoprint.ResourceFetcher):
    def fetch_url(self, url: str):
        if url.startswith("font://"):
            font_path = Path("fonts").joinpath(url.replace("font://", ""))
            with open(font_path, "rb") as f:
                data = f.read()
                
            if font_path.suffix == ".otf":
                return plutoprint.ResourceData(data, "font/otf")
            elif font_path.suffix == ".woff":
                return plutoprint.ResourceData(data, "font/woff")
            elif font_path.suffix == ".woff2":
                return plutoprint.ResourceData(data, "font/woff2")
        
        if url.startswith("https://i.ppy.sh/"):
            real_url_hex = url.rsplit("/",maxsplit=1)[1]
            real_url = bytes.fromhex(real_url_hex).decode("utf-8")

            with httpx.Client(base_url=real_url,verify=False) as client:
                response = client.get(url)
                if response.status_code == 200:
                    res_dict = self.convert_image(response)
                    return plutoprint.ResourceData(**res_dict)

        return super().fetch_url(url)
    
    def convert_image(self, response:httpx.Response) -> dict:
        match response.headers["content-type"]:
            case "image/vnd.microsoft.icon":
                icon_data = Image.open(io.BytesIO(response.content))
                data = io.BytesIO()
                icon_data.save(data, "png")
                data.seek(0)
                return {"content":data.getvalue(), "mime_type":"image/png"}
            case _:
                return {"content":response.content, "mime_type":response.headers["content-type"]}

    
def get_user_json(osu_id:int) -> dict:
    with httpx.Client(base_url="https://osu.ppy.sh",verify=False) as client:
        response = client.get(f"users/{osu_id}")
        if response.status_code == 200:
            reasult = GET_USER_JSON.search(response.text)
            if reasult:
                return json.loads(html.unescape(str(reasult.group(1))))

        return {}


def get_profile_image(user_id:int) -> None:

    data = get_user_json(user_id)

    with open("template.html", "r", encoding="utf-8") as f:
        html = f.read()
    with open("template.css", "r", encoding="utf-8") as f:
        css = f.read()
        
    html = html.replace(r"{{user_page_html}}", data["user"]["page"]["html"])
    css = css.replace(r"{{user_profile_hue}}", str(data["user"]["profile_hue"]))

    book = plutoprint.Book(
        size=plutoprint.PageSize(1000,-1), 
        margins=plutoprint.PAGE_MARGINS_NONE,
        media=plutoprint.MEDIA_TYPE_PRINT
    )
    book.custom_resource_fetcher = DataFeather()

    with open("template_debug.html", "w", encoding="utf-8") as f:
        html_debug = html + "<style>" + css + "</style>"
        f.write(html_debug)
    data = io.BytesIO()
    book.load_html(html, user_style=css)

    doc_height = book.get_document_height()
    if doc_height > MAX_HEIGHT:
        image_height = MAX_HEIGHT
    else:
        image_height = doc_height
    
    book.write_to_png_stream(data,height=int(image_height))
    if data.tell() <= QQ_PNG_SIZE_MAX:
        f = open(f"{user_id}.png", "wb")
        f.write(data.read())
        f.close()
        return

    data.seek(0)
    image = Image.open(data)

    if image_height <= WEBP_MAX:
        image.save(f"{user_id}.webp")
        
    else:
        image.save(f"{user_id}.jpeg")

if __name__ == "__main__":
    start_time = time.time()
    get_profile_image(15846580)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
