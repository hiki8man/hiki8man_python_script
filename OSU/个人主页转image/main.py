import plutoprint
import io
import httpx
import json
import re
import html
import imgkit
from pathlib import Path

GET_USER_JSON = re.compile(r'data-initial-data="(.*)"\s+data-react="profile-page"')
KIT = Path().joinpath("wkhtmltox","bin","wkhtmltoimage.exe")
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


def get_profile_image(user_id:int) -> bytes:

    data = get_user_json(user_id)
    with open("template2.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace(r"{{user_page_html}}", data["user"]["page"]["html"])
    html = html.replace(r"{{user_profile_hue}}", str(data["user"]["profile_hue"]))

    book = plutoprint.Book(size=plutoprint.PageSize(1000,-1),media=plutoprint.MEDIA_TYPE_SCREEN)
    book.load_html(html)

    data = io.BytesIO()
    book.write_to_png_stream(data)
    data.seek(0)
    
    return  data.getvalue()


if __name__ == "__main__":
    data = get_profile_image(15846580)
    with open("test.png", "wb") as f:
        f.write(data)