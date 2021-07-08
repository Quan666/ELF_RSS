# -*- coding: UTF-8 -*-

import asyncio
import base64
import bbcode
import codecs
import difflib
import hashlib
import json
import os.path
import random
import re
import sqlite3
import time
import imagehash
import tenacity
import unicodedata
from io import BytesIO
from pathlib import Path
from typing import Dict, Any
from html import unescape as html_unescape

import emoji
import feedparser
import httpx
import nonebot
from google_trans_new import google_translator
from nonebot.exception import NetworkError
from nonebot.log import logger
from PIL import Image, UnidentifiedImageError
from pyquery import PyQuery as Pq
from tenacity import retry, stop_after_attempt, stop_after_delay

from ..config import config
from . import rss_class, translation_baidu
from .qbittorrent_download import start_down

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


# 代理
def get_proxy(open_proxy: bool) -> dict:
    if not open_proxy:
        return {}
    proxy = config.rss_proxy
    return (
        httpx.Proxy(
            url="http://" + proxy,
            # May be "TUNNEL_ONLY" or "FORWARD_ONLY". Defaults to "DEFAULT".
            mode="TUNNEL_ONLY",
        )
        if proxy
        else {}
    )


STATUS_CODE = [200, 301, 302]
# 去掉烦人的 returning true from eof_received() has no effect when using ssl httpx 警告
asyncio.log.logger.setLevel(40)
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Connection": "keep-alive",
    "Content-Type": "application/xml; charset=utf-8",
}


# 入口
async def start(rss: rss_class.Rss) -> None:
    # 网络加载 新RSS
    # 读取 旧RSS 记录
    # 检查更新
    # 对更新的 RSS 记录列表进行处理，当发送成功后才写入，成功一条写一条

    try:
        new_rss = await get_rss(rss)
        new_rss_list = new_rss.get("entries")
    except tenacity.RetryError as e:
        if rss.cookies:
            cookies_str = "\n如果设置了 cookies 请检查 cookies 正确性"
        else:
            cookies_str = ""
        logger.error(
            f"{rss.name}[{rss.get_url()}]抓取失败！已达最大重试次数！请检查订阅地址！{cookies_str}\nE: {e}"
        )
        return
    old_rss = read_rss(rss.name)
    old_rss_list = old_rss.get("entries")
    if not old_rss:
        write_rss(name=rss.name, new_rss=new_rss)
        logger.info(f"{rss.name} 第一次抓取成功！")
        return

    change_rss_list = await check_update(new=new_rss_list, old=old_rss_list)
    if len(change_rss_list) <= 0:
        # 没有更新，返回
        logger.info(f"{rss.name} 没有新信息")
        return
    # 检查是否启用去重 使用 duplicate_filter_mode 字段
    conn = None
    if rss.duplicate_filter_mode:
        conn = sqlite3.connect(FILE_PATH + "cache.db")
        await cache_db_manage(conn)
    item_count = 0
    for item in change_rss_list:
        summary = (
            item["content"][0].get("value") if item.get("content") else item["summary"]
        )
        # 检查是否包含屏蔽词
        if config.black_word and re.findall("|".join(config.black_word), summary):
            logger.info("内含屏蔽词，已经取消推送该消息")
            write_item(rss=rss, new_rss=new_rss, new_item=item)
            continue
        # 检查是否匹配关键词 使用 down_torrent_keyword 字段
        if rss.down_torrent_keyword and not re.search(
            rss.down_torrent_keyword, summary
        ):
            write_item(rss=rss, new_rss=new_rss, new_item=item)
            continue
        # 检查是否匹配黑名单关键词 使用 black_keyword 字段
        if rss.black_keyword and (
            re.search(rss.black_keyword, item["title"])
            or re.search(rss.black_keyword, summary)
        ):
            write_item(rss=rss, new_rss=new_rss, new_item=item)
            continue
        # 检查是否启用去重 使用 duplicate_filter_mode 字段
        tuple_temp = None
        if rss.duplicate_filter_mode:
            tuple_temp = await duplicate_exists(
                rss=rss,
                conn=conn,
                link=item["link"],
                title=item["title"],
                summary=summary,
            )
            if tuple_temp[0]:
                write_item(rss=rss, new_rss=new_rss, new_item=item)
                continue
        # 检查是否只推送有图片的消息
        if (rss.only_pic or rss.only_has_pic) and not re.search(
            r"<img.+?>|\[img]", summary
        ):
            logger.info(f"{rss.name} 已开启仅图片/仅含有图片，该消息没有图片，将跳过")
            write_item(rss=rss, new_rss=new_rss, new_item=item)
            continue

        item_msg = f"【{new_rss.get('feed').get('title')}】更新了!\n----------------------\n"
        # 处理标题
        title = item["title"]
        if not config.blockquote:
            title = re.sub(r" - 转发 .*", "", title)
        title_msg = await handle_title(title=title)
        if not rss.only_title:
            # 先判断与正文相识度，避免标题正文一样，或者是标题为正文前N字等情况
            try:
                summary_html = Pq(summary)
                if not config.blockquote:
                    summary_html.remove("blockquote")
                similarity = difflib.SequenceMatcher(
                    None, summary_html.text()[: len(title)], title
                )
                # 标题正文相似度
                if rss.only_pic or similarity.ratio() <= 0.6:
                    item_msg += title_msg
                    if rss.translation:
                        item_msg += await handle_translation(content=title)
                # 处理正文
                item_msg += await handle_summary(summary=summary, rss=rss)
            except Exception as e:
                logger.info(f"{rss.name} 没有正文内容！ E: {e}")
                if title_msg not in item_msg:
                    item_msg += title_msg
        else:
            item_msg += title_msg
            if rss.translation:
                item_msg += await handle_translation(content=title)

        # 处理来源
        item_msg += await handle_source(source=item["link"])

        # 处理时间
        date = item.get("published_parsed")
        if not date:
            date = item.get("updated_parsed")
        item_msg += await handle_date(date=date)

        # 处理种子
        try:
            hash_list = await handle_down_torrent(rss=rss, item=item)
            if hash_list and hash_list[0] is not None:
                item_msg += "\n磁力：\n"
                for h in hash_list:
                    item_msg += f"magnet:?xt=urn:btih:{h}\n"
                item_msg = item_msg[:-1]
        except Exception as e:
            logger.error(f"下载种子时出错：{e}")
        # 发送消息并写入文件
        if await send_msg(rss=rss, msg=item_msg, item=item):
            write_item(rss=rss, new_rss=new_rss, new_item=item)
            item_count += 1
            if tuple_temp:
                await insert_into_cache_db(
                    conn=conn, item=item, image_hash=tuple_temp[1]
                )
    if item_count > 0:
        logger.info(f"{rss.name} 新消息推送完毕，共计：{item_count}")
    else:
        logger.info(f"{rss.name} 没有新信息")
    if conn is not None:
        conn.close()


# 消息发送后存入去重数据库
async def insert_into_cache_db(
    conn: sqlite3.connect, item: dict, image_hash: str
) -> None:
    cursor = conn.cursor()
    link = item["link"].replace("'", "''")
    title = item["title"].replace("'", "''")
    cursor.execute(
        f"INSERT INTO main (link, title, image_hash) VALUES ('{link}', '{title}', '{image_hash}');"
    )
    cursor.close()
    conn.commit()


# 对去重数据库进行管理
async def cache_db_manage(conn: sqlite3.connect) -> None:
    cursor = conn.cursor()
    # 用来去重的 sqlite3 数据表如果不存在就创建一个
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS main (
        "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "link" TEXT,
        "title" TEXT,
        "image_hash" TEXT,
        "datetime" TEXT DEFAULT (DATETIME('Now', 'LocalTime'))
    );
    """
    )
    cursor.close()
    conn.commit()
    cursor = conn.cursor()
    # 移除超过 config.db_cache_expire 天没重复过的记录
    cursor.execute(
        f"DELETE FROM main WHERE datetime <= DATETIME('Now', 'LocalTime', '-{config.db_cache_expire} Day');"
    )
    cursor.close()
    conn.commit()


# 去重判断
async def duplicate_exists(
    rss: rss_class.Rss, conn: sqlite3.connect, link: str, title: str, summary: str
) -> tuple:
    flag = False
    link = link.replace("'", "''")
    title = title.replace("'", "''")
    image_hash = None
    cursor = conn.cursor()
    sql = "SELECT * FROM main WHERE 1=1"
    for mode in rss.duplicate_filter_mode:
        if mode == "image":
            try:
                summary_doc = Pq(summary)
            except Exception as e:
                logger.warning(e)
                # 没有正文内容直接跳过
                continue
            img_doc = summary_doc("img")
            # 只处理仅有一张图片的情况
            if len(img_doc) != 1:
                continue
            url = img_doc.attr("src")
            # 通过图像的指纹来判断是否实际是同一张图片
            content = await download_image(url, rss.img_proxy)
            if not content:
                continue
            try:
                im = Image.open(BytesIO(content))
            except UnidentifiedImageError:
                continue
            image_hash = imagehash.average_hash(im)
            # GIF 图片的 image_hash 实际上是第一帧的值，为了避免误伤直接跳过
            if im.format == "GIF":
                continue
            logger.debug(f"image_hash: {image_hash}")
            sql += f" AND image_hash='{image_hash}'"
        if mode == "link":
            sql += f" AND link='{link}'"
        if mode == "title":
            sql += f" AND title='{title}'"
    if "or" in rss.duplicate_filter_mode:
        sql = sql.replace("AND", "OR").replace("OR", "AND", 1)
    cursor.execute(f"{sql};")
    result = cursor.fetchone()
    if result is not None:
        result_id = result[0]
        cursor.execute(
            f"UPDATE main SET datetime = DATETIME('Now','LocalTime') WHERE id = {result_id};"
        )
        cursor.close()
        conn.commit()
        flag = True
    return flag, image_hash


# 写入单条消息
def write_item(rss: rss_class.Rss, new_rss: dict, new_item: str):
    tmp = [new_item]
    write_rss(name=rss.name, new_rss=new_rss, new_item=tmp)


# 下载种子判断
async def handle_down_torrent(rss: rss_class, item: dict) -> list:
    if not rss.is_open_upload_group:
        rss.group_id = []
    if rss.down_torrent:
        return await down_torrent(rss=rss, item=item, proxy=get_proxy(rss.img_proxy))


# 创建下载种子任务
async def down_torrent(rss: rss_class, item: dict, proxy=None) -> list:
    hash_list = []
    for tmp in item["links"]:
        if (
            tmp["type"] == "application/x-bittorrent"
            or tmp["href"].find(".torrent") > 0
        ):
            hash_list.append(
                await start_down(
                    url=tmp["href"],
                    group_ids=rss.group_id,
                    name=rss.name,
                    proxy=proxy,
                )
            )
    return hash_list


# 获取 RSS 并解析为 json ，失败重试
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def get_rss(rss: rss_class.Rss) -> dict:
    # 判断是否使用cookies
    if rss.cookies:
        cookies = rss.cookies
    else:
        cookies = None

    # 获取 xml
    async with httpx.AsyncClient(
        proxies=get_proxy(open_proxy=rss.img_proxy), cookies=cookies, headers=HEADERS
    ) as client:
        d = None
        try:
            r = await client.get(rss.get_url())
            # 解析为 JSON
            d = feedparser.parse(r.content)
        except Exception:
            # logger.error("抓取订阅 {} 的 RSS 失败，将重试 ！ E：{}".format(rss.name, e))
            if (
                not re.match("[hH][tT]{2}[pP][sS]?://", rss.url, flags=0)
                and config.rsshub_backup
            ):
                logger.warning("RSSHub :" + config.rsshub + " 访问失败 ！将使用备用RSSHub 地址！")
                for rsshub_url in list(config.rsshub_backup):
                    async with httpx.AsyncClient(
                        proxies=get_proxy(open_proxy=rss.img_proxy)
                    ) as fork_client:
                        try:
                            r = await fork_client.get(rss.get_url(rsshub=rsshub_url))
                        except Exception:
                            logger.warning(
                                "RSSHub :"
                                + rss.get_url(rsshub=rsshub_url)
                                + " 访问失败 ！将使用备用 RSSHub 地址！"
                            )
                            continue
                        if r.status_code in STATUS_CODE:
                            d = feedparser.parse(r.content)
                            if d.get("entries"):
                                logger.info(rss.get_url(rsshub=rsshub_url) + " 抓取成功！")
                                break
        try:
            if not d:
                raise Exception
        except Exception:
            logger.warning(f"{rss.name} 抓取失败！将重试最多 5 次！")
            raise
        return d


# 处理标题
async def handle_title(title: str) -> str:
    return f"标题：{title}\n"


# 处理正文，图片放后面
async def handle_summary(summary: str, rss: rss_class.Rss) -> str:
    # 处理 summary 使其 HTML标签统一，方便处理
    try:
        summary_html = Pq(summary)
    except Exception as e:
        logger.info(f"{rss.name} 没有正文内容！ E: {e}")
        return ""
    # 最终消息初始化
    res_msg = ""

    # 判断是否保留转发内容，保留的话只去掉标签，留下里面的内容
    if config.blockquote:
        blockquote_html = summary_html("blockquote")
        for blockquote in blockquote_html.items():
            blockquote.replace_with(blockquote.html())
    else:
        summary_html.remove("blockquote")

    # 判断是否开启了 仅仅推送有图片的信息
    if not rss.only_pic:
        # 处理标签及翻译
        summary_text = await handle_html_tag(html=summary_html)
        # 移除指定内容
        if rss.content_to_remove:
            for pattern in rss.content_to_remove:
                summary_text = re.sub(pattern, "", summary_text)
        res_msg += summary_text
        # 翻译处理后的正文
        if rss.translation:
            res_msg += await handle_translation(content=summary_text)

    # 处理图片
    res_msg += await handle_img(
        html=summary_html, img_proxy=rss.img_proxy, img_num=rss.max_image_number
    )

    return res_msg + "\n"


# 处理来源
async def handle_source(source: str) -> str:
    # 缩短 pixiv 链接
    str_link = re.sub("https://www.pixiv.net/artworks/", "https://pixiv.net/i/", source)
    # issue 36 处理链接
    if re.search(r"^//", source):
        str_link = str_link.replace("//", "https://")
    return "链接：" + str_link + "\n"


# 处理日期
async def handle_date(date=None) -> str:
    if date:
        rss_time = time.mktime(date)
        # 时差处理，待改进
        if rss_time + 28800.0 < time.time():
            rss_time += 28800.0
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime(rss_time))
    # 没有日期的情况，以当前时间
    else:
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime())


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
        try:
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
        except BaseException as e:
            logger.error(f"图片和谐失败！ E: {e}")
            raise
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
async def fuck_pixiv(url: str) -> str:
    if url.find("pixiv.cat"):
        img_id = re.sub("https://pixiv.cat/", "", url)
        img_id = img_id[:-4]
        info_list = img_id.split("-")
        async with httpx.AsyncClient(proxies={}) as client:
            try:
                req_json = (
                    await client.get(
                        "https://hibiapi.getloli.com/api/pixiv/illust?id="
                        + info_list[0]
                    )
                ).json()
                if len(info_list) >= 2:
                    return req_json["illust"]["meta_pages"][int(info_list[1]) - 1][
                        "image_urls"
                    ]["original"]
                else:
                    return req_json["illust"]["meta_single_page"]["original_image_url"]
            except Exception as e:
                logger.error(f"处理pixiv.cat链接时出现问题 ：{e}")
                return url
    else:
        return url


@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def download_image_detail(url: str, proxy: bool):
    try:
        # 默认超时时长为 5 秒,为了减少超时前图片没完成下载的发生频率,暂时先禁用后观察
        async with httpx.AsyncClient(
            proxies=get_proxy(open_proxy=proxy), timeout=None
        ) as client:
            if config.close_pixiv_cat:
                url = await fuck_pixiv(url=url)
            referer = re.findall("([hH][tT]{2}[pP][sS]?://.*?)/.*?", url)[0]
            headers = {"referer": referer}
            try:
                pic = await client.get(url, headers=headers)
            except httpx.ConnectError as e:
                logger.error(f"图片[{url}]下载失败,有可能需要开启代理！ \n{e}")
                return None
            # 如果 图片无法获取到 / 获取到的不是图片，直接返回
            if ("image" not in pic.headers["Content-Type"]) or (
                pic.status_code not in STATUS_CODE
            ):
                logger.error(
                    f"[{url}] Content-Type: {pic.headers['Content-Type']} status_code: {pic.status_code}"
                )
                return None
            return pic.content
    except Exception as e:
        logger.error(f"图片[{url}]下载失败,将重试 \n{e}")
        raise


# 图片地址预处理
async def handle_img_url(url: str) -> str:
    if re.search(r"^//", url):
        url = url.replace("//", "https://")
    # 如果是推特图片，重定向为原图
    if "pbs.twimg.com" in url:
        url = url.replace("?format=", ".").replace("&name=", ":")
        url = re.sub(":(thumb|small|medium|large)", "", url)
        if ":orig" not in url:
            url += ":orig"
    return url


async def download_image(url: str, proxy: bool = False):
    url = await handle_img_url(url)
    try:
        return await download_image_detail(url=url, proxy=proxy)
    except Exception as e:
        logger.error(f"图片[{url}]下载失败！已达最大重试次数！{e}")
        return None


async def handle_img_combo(url: str, img_proxy: bool) -> str:
    url = await handle_img_url(url)
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


# HTML标签等处理
async def handle_html_tag(html) -> str:
    rss_str = html_unescape(str(html))

    # issue 36 处理 bbcode
    rss_str = re.sub(
        r"(\[url=.+?])?\[img].+?\[/img](\[/url])?", "", rss_str, flags=re.I
    )
    bbcode_tags = [
        "align",
        "backcolor",
        "color",
        "font",
        "size",
        "table",
        "url",
        "b",
        "u",
        "tr",
        "td",
        "tbody",
    ]
    for i in bbcode_tags:
        rss_str = re.sub(rf"\[{i}=.+?]", "", rss_str, flags=re.I)
        rss_str = re.sub(rf"\[/?{i}]", "", rss_str, flags=re.I)

    # 去掉结尾被截断的信息
    rss_str = re.sub(
        r"(\[[^]]+|\[img][^\[\]]+) \.\.\n?</p>", "</p>", rss_str, flags=re.I
    )

    # 检查正文是否为 bbcode ，没有成对的标签也当作不是，从而不进行处理
    bbcode_search = re.search(r"\[/(\w+)]", rss_str)
    if bbcode_search and re.search(rf"\[{bbcode_search.group(1)}", rss_str):
        parser = bbcode.Parser()
        parser.escape_html = False
        rss_str = parser.format(rss_str)

    new_html = Pq(rss_str)
    # 有序/无序列表 标签处理
    for ul in new_html("ul").items():
        for li in ul("li").items():
            li_str_search = re.search("<li>(.+)</li>", repr(str(li)))
            rss_str = rss_str.replace(str(li), f"\n- {li_str_search.group(1)}").replace(
                "\\n", "\n"
            )
    for ol in new_html("ol").items():
        for index, li in enumerate(ol("li").items()):
            li_str_search = re.search("<li>(.+)</li>", repr(str(li)))
            rss_str = rss_str.replace(
                str(li), f"\n{index + 1}. {li_str_search.group(1)}"
            ).replace("\\n", "\n")
    rss_str = re.sub("</?(ul|ol)>", "", rss_str)
    # 处理没有被 ul / ol 标签包围的 li 标签
    rss_str = rss_str.replace("<li>", "- ").replace("</li>", "")

    # <a> 标签处理
    for a in new_html("a").items():
        a_str = re.search(r"<a.+?</a>", html_unescape(str(a)), flags=re.DOTALL)[0]
        if a.text() and str(a.text()) != a.attr("href"):
            rss_str = rss_str.replace(a_str, f" {a.text()}: {a.attr('href')}\n")
        else:
            rss_str = rss_str.replace(a_str, f" {a.attr('href')}\n")

    # 处理一些 HTML 标签
    html_tags = [
        "b",
        "i",
        "p",
        "code",
        "del",
        "div",
        "dd",
        "dl",
        "dt",
        "font",
        "iframe",
        "pre",
        "small",
        "span",
        "strong",
        "sub",
        "table",
        "td",
        "th",
        "tr",
    ]
    # 直接去掉标签，留下内部文本信息
    for i in html_tags:
        rss_str = re.sub(rf'<{i} .+?"/?>', "", rss_str)
        rss_str = re.sub(rf"</?{i}>", "", rss_str)

    rss_str = re.sub('<br .+?"/>|<(br|hr) ?/?>', "\n", rss_str)
    rss_str = re.sub(r"</?h\d>", "\n", rss_str)

    # 删除图片、视频标签
    rss_str = re.sub(r'<video .+?"?/>|</video>|<img.+?>', "", rss_str)

    # 去掉多余换行
    while re.search("\n\n", rss_str):
        rss_str = re.sub("\n\n", "\n", rss_str)

    if 0 < config.max_length < len(rss_str):
        rss_str = rss_str[: config.max_length] + "..."

    return rss_str


# 翻译
async def handle_translation(content: str) -> str:
    translator = google_translator()
    try:
        text = emoji.demojize(content)
        text = re.sub(r":[A-Za-z_]*:", " ", text)
        if config.baidu_id and config.baidu_key:
            content = re.sub(r"\n", "百度翻译 ", content)
            content = unicodedata.normalize("NFC", content)
            text = emoji.demojize(content)
            text = re.sub(r":[A-Za-z_]*:", " ", text)
            text = "\n翻译(BaiduAPI)：\n" + str(
                translation_baidu.baidu_translate(re.escape(text))
            )
        else:
            text = "\n翻译：\n" + str(translator.translate(re.escape(text), lang_tgt="zh"))
        text = re.sub(r"\\", "", text)
        text = re.sub(r"百度翻译", "\n", text)
    except Exception as e:
        text = "\n翻译失败！" + str(e) + "\n"
    return text


# 将 dict 对象转换为 json 字符串后，计算哈希值，供后续比较
def dict_hash(dictionary: Dict[str, Any]) -> str:
    keys = ["id", "link", "published", "updated", "title"]
    dictionary_temp = {k: dictionary[k] for k in keys if k in dictionary}
    d_hash = hashlib.md5()
    encoded = json.dumps(dictionary_temp, sort_keys=True).encode()
    d_hash.update(encoded)
    return d_hash.hexdigest()


# 检查更新
async def check_update(new: list, old: list) -> list:
    old_hash_list = [dict_hash(i) if not i.get("hash") else i.get("hash") for i in old]
    # 对比本地消息缓存和获取到的消息，新的存入 hash ，随着检查更新的次数增多，逐步替换原来没存 hash 的缓存记录
    temp = []
    for i in new:
        hash_temp = dict_hash(i)
        if hash_temp not in old_hash_list:
            i["hash"] = hash_temp
            temp.append(i)
    # 将结果进行去重，避免消息重复发送
    result = [
        value for index, value in enumerate(temp) if value not in temp[index + 1 :]
    ]
    # 对结果按照发布时间排序
    result_with_date = [
        (await handle_date(i.get("updated_parsed")), i)
        if i.get("updated_parsed")
        else (await handle_date(i.get("published_parsed")), i)
        for i in result
    ]
    result_with_date.sort(key=lambda tup: tup[0])
    result = [i for key, i in result_with_date]
    return result


# 读取记录
def read_rss(name) -> dict:
    # 检查是否存在rss记录
    json_path = FILE_PATH + (name + ".json")
    if not os.path.isfile(json_path) or os.stat(json_path).st_size == 0:
        return {}
    with codecs.open(json_path, "r", "utf-8") as load_f:
        load_dict = json.load(load_f)
    return load_dict


# 写入记录
def write_rss(name: str, new_rss: dict, new_item: list = None):
    if new_item:
        max_length = len(new_rss.get("entries"))
        # 防止 rss 超过设置的缓存条数
        if max_length >= config.limit:
            limit = max_length + config.limit
        else:
            limit = config.limit
        old = read_rss(name)
        for tmp in new_item:
            old["entries"].insert(0, tmp)
        old["entries"] = old["entries"][0:limit]
    else:
        old = new_rss
    if not os.path.isdir(FILE_PATH):
        os.makedirs(FILE_PATH)
    with codecs.open(FILE_PATH + (name + ".json"), "w", "utf-8") as dump_f:
        dump_f.write(json.dumps(old, sort_keys=True, indent=4, ensure_ascii=False))


# 发送消息
async def send_msg(rss: rss_class.Rss, msg: str, item: dict) -> bool:
    (bot,) = nonebot.get_bots().values()
    try:
        if len(msg) <= 0:
            return False
        if rss.user_id:
            for user_id in rss.user_id:
                try:
                    await bot.send_msg(
                        message_type="private", user_id=user_id, message=str(msg)
                    )
                except NetworkError as e:
                    logger.error(f"网络错误,消息发送失败,将重试 E: {e}\n链接：{item['link']}")
                except Exception as e:
                    logger.error(f"QQ号[{user_id}]不合法或者不是好友 E: {e}")

        if rss.group_id:
            for group_id in rss.group_id:
                try:
                    await bot.send_msg(
                        message_type="group", group_id=group_id, message=str(msg)
                    )
                except NetworkError as e:
                    logger.error(f"网络错误,消息发送失败,将重试 E: {e}\n链接：{item['link']}")
                except Exception as e:
                    logger.info(f"群号[{group_id}]不合法或者未加群 E: {e}")
        return True
    except Exception as e:
        logger.info(f"发生错误 消息发送失败 E: {e}")
        return False
