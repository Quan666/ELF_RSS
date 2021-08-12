import base64
import httpx
import random
import re

from PIL import Image, UnidentifiedImageError
from io import BytesIO
from nonebot import logger
from pyquery import PyQuery as Pq
from tenacity import retry, stop_after_attempt, stop_after_delay

from .utils import get_proxy
from ....config import config

STATUS_CODE = [200, 301, 302]


# 通过 ezgif 压缩 GIF
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def resize_gif(url: str, proxy: bool, resize_ratio: int = 2) -> BytesIO:
    try:
        async with httpx.AsyncClient(proxies=get_proxy(proxy)) as client:
            response = await client.post(
                url="https://s3.ezgif.com/resize",
                data={"new-image-url": url},
                timeout=None,
            )
            d = Pq(response.text)
            next_url = d("form").attr("action")
            file = d("form > input[type=hidden]:nth-child(1)").attr("value")
            token = d("form > input[type=hidden]:nth-child(2)").attr("value")
            old_width = d("form > input[type=hidden]:nth-child(3)").attr("value")
            old_height = d("form > input[type=hidden]:nth-child(4)").attr("value")
            data = {
                "file": file,
                "token": token,
                "old_width": old_width,
                "old_height": old_height,
                "width": str(int(old_width) // resize_ratio),
                "method": "gifsicle",
                "ar": "force",
            }
            async with httpx.AsyncClient(proxies=get_proxy(proxy)) as fork_client:
                response = await fork_client.post(
                    url=next_url + "?ajax=true", data=data, timeout=None
                )
                d = Pq(response.text)
                output_img_url = "https:" + d("img:nth-child(1)").attr("src")
                return await download_image(output_img_url)
    except Exception as e:
        logger.error(f"GIF 图片[{url}]压缩失败,将重试 \n {e}")


# 图片压缩
async def zip_pic(url: str, proxy: bool, content: bytes):
    # 打开一个 JPEG/PNG/GIF 图像文件
    try:
        im = Image.open(BytesIO(content))
    except UnidentifiedImageError:
        logger.error(f"无法识别图像文件 链接：[{url}]")
        return None
    # 获得图像文件类型：
    file_type = im.format
    if file_type != "GIF":
        # 对图像文件进行缩小处理
        im.thumbnail((config.zip_size, config.zip_size))
        width, height = im.size
        logger.debug(f"Resize image to: {width} x {height}")
        # 和谐
        pim = im.load()
        points = [[0, 0], [width - 1, 0], [0, height - 1], [width - 1, height - 1]]
        for point in points:
            if file_type == "PNG":
                im.putpixel(point, random.randint(0, 255))
            elif file_type == "JPEG":
                # 如果 Image.getcolors() 返回有值,说明不是 RGB 三通道图,而是单通道图
                if im.getcolors():
                    pim[point[0], point[1]] = random.randint(0, 255)
                else:
                    pim[point[0], point[1]] = (
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    )
            return im
    else:
        if len(content) > config.gif_zip_size * 1024:
            return await resize_gif(url, proxy)
        return BytesIO(content)


# 将图片转化为 base64
async def get_pic_base64(content) -> str:
    if not content:
        return ""
    elif isinstance(content, bytes):
        image_buffer = BytesIO(content)
    elif isinstance(content, BytesIO):
        image_buffer = content
    else:
        image_buffer = BytesIO()
        content.save(image_buffer, format=content.format)
    res = str(base64.b64encode(image_buffer.getvalue()), encoding="utf-8")
    return res


# 去你的 pixiv.cat
async def fuck_pixiv_cat(url: str) -> str:
    img_id = re.sub("https://pixiv.cat/", "", url)
    img_id = img_id[:-4]
    info_list = img_id.split("-")
    async with httpx.AsyncClient(proxies={}) as client:
        try:
            req_json = (
                await client.get(
                    f"https://api.obfs.dev/api/pixiv/illust?id={info_list[0]}"
                )
            ).json()
            if len(info_list) >= 2:
                return req_json["illust"]["meta_pages"][int(info_list[1]) - 1][
                    "image_urls"
                ]["original"]
            else:
                return req_json["illust"]["meta_single_page"]["original_image_url"]
        except Exception as e:
            logger.error(f"处理pixiv.cat链接时出现问题 ：{e} 链接：[{url}]")
            return url


@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def download_image_detail(url: str, proxy: bool):
    try:
        # 默认超时时长为 5 秒,为了减少超时前图片没完成下载的发生频率,暂时先禁用后观察
        async with httpx.AsyncClient(
            proxies=get_proxy(open_proxy=proxy), timeout=None
        ) as client:
            referer = re.findall("([hH][tT]{2}[pP][sS]?://.*?)/.*?", url)[0]
            headers = {"referer": referer}
            try:
                pic = await client.get(url, headers=headers)
            except httpx.ConnectError as e:
                logger.error(f"图片[{url}]下载失败,有可能需要开启代理！ \n{e}")
                return None
            # 如果图片无法获取到，直接返回
            if (len(pic.content) == 0) or (pic.status_code not in STATUS_CODE):
                if "pixiv.cat" in url:
                    url = await fuck_pixiv_cat(url=url)
                    return await download_image(url, proxy)
                logger.error(
                    f"[{url}] Content-Type: {pic.headers['Content-Type']} status_code: {pic.status_code}"
                )
                return None
            return pic.content
    except Exception as e:
        logger.error(f"图片[{url}]下载失败,将重试 \n{e}")
        raise


async def download_image(url: str, proxy: bool = False):
    try:
        return await download_image_detail(url=url, proxy=proxy)
    except Exception as e:
        logger.error(f"图片[{url}]下载失败！已达最大重试次数！{e}")
        return None


async def handle_img_combo(url: str, img_proxy: bool) -> str:
    content = await download_image(url, img_proxy)
    resize_content = await zip_pic(url, img_proxy, content)
    img_base64 = await get_pic_base64(resize_content)
    if img_base64:
        return f"[CQ:image,file=base64://{img_base64}]"
    return f"\n图片走丢啦: {url}\n"


# 处理图片、视频
async def handle_img(html, img_proxy: bool, img_num: int) -> str:
    img_str = ""
    # 处理图片
    doc_img = list(html("img").items())
    # 只发送限定数量的图片，防止刷屏
    if 0 < img_num < len(doc_img):
        img_str += f"\n因启用图片数量限制，目前只有 {img_num} 张图片："
        doc_img = doc_img[:img_num]
    for img in doc_img:
        url = img.attr("src")
        img_str += await handle_img_combo(url, img_proxy)

    # 处理视频
    doc_video = html("video")
    if doc_video:
        img_str += "\n视频封面："
        for video in doc_video.items():
            url = video.attr("poster")
            img_str += await handle_img_combo(url, img_proxy)

    # 解决 issue 36
    img_list = re.findall(r"\[img](.+?)\[/img]", str(html), flags=re.I)
    for img_tmp in img_list:
        img_str += await handle_img_combo(img_tmp, img_proxy)

    return img_str
