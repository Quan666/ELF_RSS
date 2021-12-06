from ... import rss_class
from ...qbittorrent_download import start_down
from .utils import get_proxy


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
