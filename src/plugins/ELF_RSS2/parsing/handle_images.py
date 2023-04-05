import base64
import random
import re
from io import BytesIO
from typing import Any, Dict, Optional, Tuple, Union

import aiohttp
from nonebot.log import logger
from PIL import Image, UnidentifiedImageError
from pyquery import PyQuery as Pq
from tenacity import RetryError, retry, stop_after_attempt, stop_after_delay
from yarl import URL

from ..config import Path, config
from ..rss_class import Rss
from .utils import get_proxy, get_summary


# 通过 ezgif 压缩 GIF
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def resize_gif(url: str, resize_ratio: int = 2) -> Optional[bytes]:
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            "https://s3.ezgif.com/resize",
            data={"new-image-url": url},
        )
        d = Pq(await resp.text())
        next_url = d("form").attr("action")
        _file = d("form > input[type=hidden]:nth-child(1)").attr("value")
        token = d("form > input[type=hidden]:nth-child(2)").attr("value")
        old_width = d("form > input[type=hidden]:nth-child(3)").attr("value")
        old_height = d("form > input[type=hidden]:nth-child(4)").attr("value")
        data = {
            "file": _file,
            "token": token,
            "old_width": old_width,
            "old_height": old_height,
            "width": str(int(old_width) // resize_ratio),
            "method": "gifsicle",
            "ar": "force",
        }
        resp = await session.post(next_url, params="ajax=true", data=data)
        d = Pq(await resp.text())
        output_img_url = "https:" + d("img:nth-child(1)").attr("src")
        return await download_image(output_img_url)


# 通过 ezgif 把视频中间 4 秒转 GIF 作为预览
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def get_preview_gif_from_video(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            "https://s3.ezgif.com/video-to-gif",
            data={"new-image-url": url},
        )
        d = Pq(await resp.text())
        video_length = re.search(
            r"\d\d:\d\d:\d\d", str(d("#main > p.filestats > strong"))
        ).group()  # type: ignore
        hours = int(video_length.split(":")[0])
        minutes = int(video_length.split(":")[1])
        seconds = int(video_length.split(":")[2])
        video_length_median = (hours * 60 * 60 + minutes * 60 + seconds) // 2
        next_url = d("form").attr("action")
        _file = d("form > input[type=hidden]:nth-child(1)").attr("value")
        token = d("form > input[type=hidden]:nth-child(2)").attr("value")
        default_end = d("#end").attr("value")
        if float(default_end) >= 4:
            start = video_length_median - 2
            end = video_length_median + 2
        else:
            start = 0
            end = default_end
        data = {
            "file": _file,
            "token": token,
            "start": start,
            "end": end,
            "size": 320,
            "fps": 25,
            "method": "ffmpeg",
        }
        resp = await session.post(next_url, params="ajax=true", data=data)
        d = Pq(await resp.text())
        return f'https:{d("img:nth-child(1)").attr("src")}'


# 图片压缩
async def zip_pic(url: str, content: bytes) -> Union[Image.Image, bytes, None]:
    # 打开一个 JPEG/PNG/GIF/WEBP 图像文件
    try:
        im = Image.open(BytesIO(content))
    except UnidentifiedImageError:
        logger.error(f"无法识别图像文件 链接：[{url}]")
        return None
    if im.format != "GIF":
        # 先把 WEBP 图像转为 PNG
        if im.format == "WEBP":
            with BytesIO() as output:
                im.save(output, "PNG")
                im = Image.open(output)
        # 对图像文件进行缩小处理
        im.thumbnail((config.zip_size, config.zip_size))
        width, height = im.size
        logger.debug(f"Resize image to: {width} x {height}")
        # 和谐
        points = [(0, 0), (0, height - 1), (width - 1, 0), (width - 1, height - 1)]
        for x, y in points:
            im.putpixel((x, y), random.randint(0, 255))
        return im
    else:
        if len(content) > config.gif_zip_size * 1024:
            try:
                return await resize_gif(url)
            except RetryError:
                logger.error(f"GIF 图片[{url}]压缩失败，将发送原图")
        return content


# 将图片转化为 base64
def get_pic_base64(content: Union[Image.Image, bytes, None]) -> str:
    if not content:
        return ""
    if isinstance(content, Image.Image):
        with BytesIO() as output:
            content.save(output, format=content.format)
            content = output.getvalue()
    if isinstance(content, bytes):
        return str(base64.b64encode(content).decode())
    return ""


# 去你的 pixiv.cat
async def fuck_pixiv_cat(url: str) -> str:
    img_id = re.sub("https://pixiv.cat/", "", url)
    img_id = img_id[:-4]
    info_list = img_id.split("-")
    async with aiohttp.ClientSession() as session:
        try:
            resp = await session.get(
                f"https://api.obfs.dev/api/pixiv/illust?id={info_list[0]}"
            )
            resp_json = await resp.json()
            if len(info_list) >= 2:
                return str(
                    resp_json["illust"]["meta_pages"][int(info_list[1]) - 1][
                        "image_urls"
                    ]["original"]
                )
            else:
                return str(
                    resp_json["illust"]["meta_single_page"]["original_image_url"]
                )
        except Exception as e:
            logger.error(f"处理pixiv.cat链接时出现问题 ：{e} 链接：[{url}]")
            return url


@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def download_image_detail(url: str, proxy: bool) -> Optional[bytes]:
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        referer = f"{URL(url).scheme}://{URL(url).host}/"
        headers = {"referer": referer}
        try:
            resp = await session.get(
                url, headers=headers, proxy=get_proxy(open_proxy=proxy)
            )
            # 如果图片无法获取到，直接返回
            if len(await resp.read()) == 0:
                if "pixiv.cat" in url:
                    url = await fuck_pixiv_cat(url=url)
                    return await download_image(url, proxy)
                logger.error(
                    f"图片[{url}]下载失败！ Content-Type: {resp.headers['Content-Type']} status: {resp.status}"
                )
                return None
            # 如果图片格式为 SVG ，先转换为 PNG
            if resp.headers["Content-Type"].startswith("image/svg+xml"):
                next_url = str(
                    URL("https://images.weserv.nl/").with_query(f"url={url}&output=png")
                )
                return await download_image(next_url, proxy)
            return await resp.read()
        except Exception as e:
            logger.warning(f"图片[{url}]下载失败！将重试最多 5 次！\n{e}")
            raise


async def download_image(url: str, proxy: bool = False) -> Optional[bytes]:
    try:
        return await download_image_detail(url=url, proxy=proxy)
    except RetryError:
        logger.error(f"图片[{url}]下载失败！已达最大重试次数！有可能需要开启代理！")
        return None


async def handle_img_combo(url: str, img_proxy: bool, rss: Optional[Rss] = None) -> str:
    """'
    下载图片并返回可用的CQ码

    参数:
        url: 需要下载的图片地址
        img_proxy: 是否使用代理下载图片
        rss: Rss对象
    返回值:
        返回当前图片的CQ码,以base64格式编码发送
        如获取图片失败将会提示图片走丢了
    """
    if content := await download_image(url, img_proxy):
        if rss is not None and rss.download_pic:
            _url = URL(url)
            logger.debug(f"正在保存图片: {url}")
            try:
                save_image(content=content, file_url=_url, rss=rss)
            except Exception as e:
                logger.warning(f"在保存图片到本地时出现错误\nE:{repr(e)}")
        if resize_content := await zip_pic(url, content):
            if img_base64 := get_pic_base64(resize_content):
                return f"[CQ:image,file=base64://{img_base64}]"
    return f"\n图片走丢啦 链接：[{url}]\n"


async def handle_img_combo_with_content(url: str, content: bytes) -> str:
    if resize_content := await zip_pic(url, content):
        if img_base64 := get_pic_base64(resize_content):
            return f"[CQ:image,file=base64://{img_base64}]"
    return f"\n图片走丢啦 链接：[{url}]\n" if url else "\n图片走丢啦\n"


# 处理图片、视频
async def handle_img(item: Dict[str, Any], img_proxy: bool, img_num: int) -> str:
    if item.get("image_content"):
        return await handle_img_combo_with_content(
            item.get("gif_url", ""), item["image_content"]
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
    if doc_video := html("video"):
        img_str += "\n视频封面："
        for video in doc_video.items():
            url = video.attr("poster")
            img_str += await handle_img_combo(url, img_proxy)

    return img_str


# 处理 bbcode 图片
async def handle_bbcode_img(html: Pq, img_proxy: bool, img_num: int) -> str:
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


def file_name_format(file_url: URL, rss: Rss) -> Tuple[Path, str]:
    """
    可以根据用户设置的规则来格式化文件名
    """
    format_rule = config.img_format or ""
    down_path = config.img_down_path or ""
    rules = {  # 替换格式化字符串
        "{subs}": rss.name,
        "{name}": file_url.name
        if "{ext}" not in format_rule
        else Path(file_url.name).stem,
        "{ext}": file_url.suffix if "{ext}" in format_rule else "",
    }
    for k, v in rules.items():
        format_rule = format_rule.replace(k, v)
    if down_path == "":  # 如果没设置保存路径的话,就保存到默认目录下
        save_path = Path().cwd() / "data" / "image"
    elif down_path[0] == ".":
        save_path = Path().cwd() / Path(down_path)
    else:
        save_path = Path(down_path)
    full_path = save_path / format_rule
    save_path = full_path.parents[0]
    save_name = full_path.name
    return save_path, save_name


def save_image(content: bytes, file_url: URL, rss: Rss) -> None:
    """
    将压缩之前的原图保存到本地的电脑上
    """
    save_path, save_name = file_name_format(file_url=file_url, rss=rss)

    full_save_path = save_path / save_name
    try:
        full_save_path.write_bytes(content)
    except FileNotFoundError:
        # 初次写入时文件夹不存在,需要创建一下
        save_path.mkdir(parents=True)
        full_save_path.write_bytes(content)
