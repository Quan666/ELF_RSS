from typing import Any, Dict, List, Optional

from ...qbittorrent_download import start_down
from ...rss_class import Rss


# 创建下载种子任务
async def down_torrent(
    rss: Rss, item: Dict[str, Any], proxy: Optional[str]
) -> List[str]:
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
