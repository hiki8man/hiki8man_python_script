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


def get_profile_image(user_id:int) -> list[bytes]:

    data = get_user_json(user_id)
    with open("template.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace(r"{{user_page_html}}", data["user"]["page"]["html"])
    html = html.replace(r"{{user_profile_hue}}", str(data["user"]["profile_hue"]))

    book = plutoprint.Book(size=plutoprint.PageSize(1000,200), margins=plutoprint.PAGE_MARGINS_NONE,media=plutoprint.MEDIA_TYPE_PRINT)
    book.load_html(html)

    # [TODO] 像zncookie这种图特别长的情况需要将图分为多个部分进行渲染，大小暂定10000
    if book.get_page_count() <= 1:
        data = io.BytesIO()
        book.write_to_png_stream(data)
        data.seek(0)
        return  [data.getvalue()]
    else:
        data_list = []
        total_pages = book.get_page_count()
        # 3. 逐页渲染
        for i in range(total_pages):
            data = io.BytesIO()
            # 获取当前页的尺寸，创建对应的画布
            page_size = book.get_page_size_at(i)
            width = page_size.width
            height = page_size.height

            # 创建画布并渲染当前页
            with plutoprint.ImageCanvas(1140, 267) as canvas:
                canvas.clear_surface(1, 1, 1) # 做一个hue转rgba
                canvas.transform(1, 0, 0, 1, -120, 0)
                book.render_page(canvas, i)  # 关键点：渲染特定页面
                canvas.write_to_png_stream(data)
                data.seek(0)
                data_list.append(data.getvalue())
        return data_list

if __name__ == "__main__":
    data_list:list[bytes] = get_profile_image(18230719)
    conut = len(data_list)
    # 修正ZnCookie超长的个人页面无法渲染的BUG
    # 需要改成yeild节省内存
    from PIL import Image
    output_image = Image.new("RGB", (1140, 267 * conut))
    for i in range(conut):
        output_image.paste(Image.open(io.BytesIO(data_list[i])), (0, 267 * i))
    
    output_image.save("output.png")

 