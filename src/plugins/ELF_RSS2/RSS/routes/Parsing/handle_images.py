import base64
import random
import re
from io import BytesIO
from typing import Union

import httpx
from nonebot import logger
from PIL import Image, UnidentifiedImageError
from pyquery import PyQuery as Pq
from tenacity import RetryError, retry, stop_after_attempt, stop_after_delay

from ....config import config
from .utils import get_proxy, get_summary

STATUS_CODE = [200, 301, 302]


# 通过 ezgif 压缩 GIF
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def resize_gif(url: str, resize_ratio: int = 2) -> Union[bytes, None]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://s3.ezgif.com/resize",
            data={"new-image-url": url},
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
        response = await client.post(url=next_url + "?ajax=true", data=data)
        d = Pq(response.text)
        output_img_url = "https:" + d("img:nth-child(1)").attr("src")
        return await download_image(output_img_url)


# 通过 ezgif 把视频中间 4 秒转 GIF 作为预览
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def get_preview_gif_from_video(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://s3.ezgif.com/video-to-gif",
            data={"new-image-url": url},
        )
        d = Pq(response.text)
        video_length = re.search(
            r"\d\d:\d\d:\d\d", str(d("#main > p.filestats > strong"))
        ).group()
        hours = int(video_length.split(":")[0])
        minutes = int(video_length.split(":")[1])
        seconds = int(video_length.split(":")[2])
        video_length_median = (hours * 60 * 60 + minutes * 60 + seconds) // 2
        next_url = d("form").attr("action")
        file = d("form > input[type=hidden]:nth-child(1)").attr("value")
        token = d("form > input[type=hidden]:nth-child(2)").attr("value")
        default_end = d("#end").attr("value")
        if float(default_end) >= 4:
            start = video_length_median - 2
            end = video_length_median + 2
        else:
            start = 0
            end = default_end
        data = {
            "file": file,
            "token": token,
            "start": start,
            "end": end,
            "size": 320,
            "fps": 25,
            "method": "ffmpeg",
        }
        response = await client.post(url=next_url + "?ajax=true", data=data)
        d = Pq(response.text)
        output_img_url = "https:" + d("img:nth-child(1)").attr("src")
    return output_img_url


# 图片压缩
async def zip_pic(url: str, content: bytes) -> Union[Image.Image, bytes, None]:
    # 打开一个 JPEG/PNG/GIF/WEBP 图像文件
    try:
        im = Image.open(BytesIO(content))
    except UnidentifiedImageError:
        logger.error(f"无法识别图像文件 链接：[{url}]")
        return None
    # 获得图像文件类型：
    file_type = im.format
    if file_type != "GIF":
        # 先把 WEBP 图像转为 PNG
        if file_type == "WEBP":
            with BytesIO() as output:
                im.save(output, "PNG")
                im = Image.open(output)
                file_type = "PNG"
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
            try:
                return await resize_gif(url)
            except RetryError:
                logger.error(f"GIF 图片[{url}]压缩失败，将发送原图")
        return content


# 将图片转化为 base64
async def get_pic_base64(content) -> str:
    if not content:
        return ""
    if isinstance(content, Image.Image):
        with BytesIO() as output:
            content.save(output, format=content.format)
            content = output.getvalue()
    if isinstance(content, bytes):
        content = str(base64.b64encode(content).decode())
    return content


# 去你的 pixiv.cat
async def fuck_pixiv_cat(url: str) -> str:
    img_id = re.sub("https://pixiv.cat/", "", url)
    img_id = img_id[:-4]
    info_list = img_id.split("-")
    async with httpx.AsyncClient() as client:
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
async def download_image_detail(url: str, proxy: bool) -> Union[bytes, None]:
    async with httpx.AsyncClient(proxies=get_proxy(open_proxy=proxy)) as client:
        referer = re.search("[hH][tT]{2}[pP][sS]?://[^/]+", url).group()
        headers = {"referer": referer}
        try:
            pic = await client.get(url, headers=headers)
        except Exception as e:
            logger.warning(f"图片[{url}]下载失败！将重试最多 5 次！\n{e}")
            raise
        # 如果图片无法获取到，直接返回
        if (len(pic.content) == 0) or (pic.status_code not in STATUS_CODE):
            if "pixiv.cat" in url:
                url = await fuck_pixiv_cat(url=url)
                return await download_image(url, proxy)
            logger.error(
                f"图片[{url}]下载失败！ Content-Type: {pic.headers.get('Content-Type')} status_code: {pic.status_code}"
            )
            return None
        return pic.content


async def download_image(url: str, proxy: bool = False) -> Union[bytes, None]:
    try:
        return await download_image_detail(url=url, proxy=proxy)
    except RetryError:
        logger.error(f"图片[{url}]下载失败！已达最大重试次数！有可能需要开启代理！")
        return None


async def handle_img_combo(url: str, img_proxy: bool) -> str:
    content = await download_image(url, img_proxy)
    resize_content = await zip_pic(url, content)
    img_base64 = await get_pic_base64(resize_content)
    if img_base64:
        return f"[CQ:image,file=base64://{img_base64}]"
    return f"\n图片走丢啦: {url}\n"


async def handle_img_combo_with_content(gif_url: str, content: bytes) -> str:
    resize_content = await zip_pic(gif_url, content)
    img_base64 = await get_pic_base64(resize_content)
    if img_base64:
        return f"[CQ:image,file=base64://{img_base64}]"
    return f"\n图片走丢啦\n"


# 处理图片、视频
async def handle_img(item: dict, img_proxy: bool, img_num: int) -> str:
    if item.get("image_content"):
        return await handle_img_combo_with_content(
            item.get("gif_url"), item.get("image_content")
        )
    html = Pq(get_summary(item))
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

    return img_str


# 处理 bbcode 图片
async def handle_bbcode_img(html, img_proxy: bool, img_num: int) -> str:
    img_str = ""
    # 处理图片
    img_list = re.findall(r"\[img[^]]*](.+)\[/img]", str(html), flags=re.I)
    # 只发送限定数量的图片，防止刷屏
    if 0 < img_num < len(img_list):
        img_str += f"\n因启用图片数量限制，目前只有 {img_num} 张图片："
        img_list = img_list[:img_num]
    for img_tmp in img_list:
        img_str += await handle_img_combo(img_tmp, img_proxy)

    return img_str
