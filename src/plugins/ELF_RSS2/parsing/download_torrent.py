import re
from typing import Any, Dict, List, Optional

import aiohttp
from nonebot.log import logger

from ..config import config
from ..parsing.utils import get_summary
from ..pikpak_offline import pikpak_offline_download
from ..qbittorrent_download import start_down
from ..rss_class import Rss
from ..utils import convert_size, get_torrent_b16_hash, send_msg


async def down_torrent(
    rss: Rss, item: Dict[str, Any], proxy: Optional[str]
) -> List[str]:
    """
    创建下载种子任务
    """
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


async def pikpak_offline(
    rss: Rss, item: Dict[str, Any], proxy: Optional[str]
) -> List[Dict[str, Any]]:
    """
    创建pikpak 离线下载任务
    下载到 config.pikpak_download_path/rss.name or find rss.pikpak_path_rex
    """
    download_infos = []
    for tmp in item["links"]:
        if (
            tmp["type"] == "application/x-bittorrent"
            or tmp["href"].find(".torrent") > 0
        ):
            url = tmp["href"]
            if not re.search(r"magnet:\?xt=urn:btih:", tmp["href"]):
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=100)
                ) as session:
                    try:
                        resp = await session.get(tmp["href"], proxy=proxy)
                        content = await resp.read()
                        url = f"magnet:?xt=urn:btih:{get_torrent_b16_hash(content)}"
                    except Exception as e:
                        msg = f"{rss.name} 下载种子失败: {e}"
                        logger.error(msg)
                        await send_msg(
                            msg=msg, user_ids=rss.user_id, group_ids=rss.group_id
                        )
                        continue
            try:
                path = f"{config.pikpak_download_path}/{rss.name}"
                summary = get_summary(item)
                if rss.pikpak_path_key and (
                    result := re.findall(rss.pikpak_path_key, summary)
                ):
                    path = (
                        config.pikpak_download_path
                        + "/"
                        + re.sub(r'[?*:"<>\\/|]', "_", result[0])
                    )
                logger.info(f"Offline download {url} to {path}")
                info = await pikpak_offline_download(url=url, path=path)
                download_infos.append(
                    {
                        "name": info["task"]["name"],
                        "file_size": convert_size(int(info["task"]["file_size"])),
                        "path": path,
                    }
                )
            except Exception as e:
                msg = f"{rss.name} PikPak 离线下载失败: {e}"
                logger.error(msg)
                await send_msg(msg=msg, user_ids=rss.user_id, group_ids=rss.group_id)
    return download_infos
