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
        
        return super().fetch_url(url)
    

    
def get_user_json(osu_id:int) -> dict:
    with httpx.Client(base_url="https://osu.ppy.sh",verify=False) as client:
        response = client.get(f"users/{osu_id}")
        if response.status_code == 200:
            reasult = GET_USER_JSON.search(response.text)
            if reasult is None:
                return {}
            else:
                return json.loads(html.unescape(str(reasult.group(1))))
        else:
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
        size=plutoprint.PageSize(1000,200), 
        margins=plutoprint.PAGE_MARGINS_NONE,
        media=plutoprint.MEDIA_TYPE_PRINT
    )
    book.custom_resource_fetcher = DataFeather()

    with open("template_debug.html", "w", encoding="utf-8") as f:
        html_debug = html + "<style>" + css + "</style>"
        f.write(html_debug)

    book.load_html(html, user_style=css)

    total_pages = book.get_page_count()
    image = Image.new("RGB", (1140, 267 * total_pages))

    with open("template_debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    for i in range(total_pages):
        data = io.BytesIO()

        with plutoprint.ImageCanvas(1140, 267) as canvas:
            canvas.clear_surface(1, 1, 1) # 做一个hue转rgba
            canvas.transform(1, 0, 0, 1, -120, 0)
            book.render_page(canvas, i)
            canvas.write_to_png_stream(data)
            data.seek(0)
            image.paste(Image.open(data), (0, 267 * i))

    if 267 * total_pages > WEBP_MAX:
        image.save(f"{user_id}.jpeg")
    else:
        image.save(f"{user_id}.webp")


if __name__ == "__main__":
    start_time = time.time()
    get_profile_image(18230719)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
