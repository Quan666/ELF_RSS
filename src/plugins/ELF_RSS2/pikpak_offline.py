from typing import Any, Dict, List
from pikpakapi.async_api import PikPakApiAsync
from pikpakapi.PikpakException import PikpakException, PikpakAccessTokenExpireException
from nonebot.log import logger

from .rss_class import Rss

from .config import config

pikpak_client = PikPakApiAsync(
    username=config.pikpak_username,
    password=config.pikpak_password,
)


async def refresh_access_token():
    """
    Login or Refresh access_token PikPak

    """
    try:
        await pikpak_client.refresh_access_token()
    except (PikpakException, PikpakAccessTokenExpireException) as e:
        await pikpak_client.login()


async def path_to_id(path: str, create: bool = False) -> List[Dict[str, Any]]:
    """
    path: str like "/1/2/3"
    create: bool create path if not exist
    将形如 /path/a/b 的路径转换为 文件夹的id
    """
    if len(path) <= 0:
        return None
    paths = path.split("/")
    paths = [p.strip() for p in paths if len(p) > 0]
    path_ids = []
    count = 0
    next_page_token = None
    parent_id = None
    while count < len(paths):
        data = await pikpak_client.file_list(
            parent_id=parent_id, next_page_token=next_page_token
        )
        id = ""
        for f in data.get("files", []):
            if f.get("kind", "") == "drive#folder" and f.get("name") == paths[count]:
                id = f.get("id")
                break
        if id:
            path_ids.append(
                {
                    "id": id,
                    "name": paths[count],
                }
            )
            count += 1
            parent_id = id
        elif data.get("next_page_token"):
            next_page_token = data.get("next_page_token")
        elif create:
            data = await pikpak_client.create_folder(
                name=paths[count], parent_id=parent_id
            )
            id = data.get("file").get("id")
            path_ids.append(
                {
                    "id": id,
                    "name": paths[count],
                }
            )
            count += 1
            parent_id = id
        else:
            break
    return path_ids


async def offline_download(
    url: str, path: str = None, parent_id: str = None, name: str = None
) -> dict:
    """
    Offline download
    当有path时, 表示下载到指定的文件夹, 否则下载到根目录
    如果存在 parent_id, 以 parent_id 为准
    """

    if not parent_id:
        path_ids = await path_to_id(path, create=True)
        if path_ids and len(path_ids) > 0:
            parent_id = path_ids[-1].get("id")
    try:
        return await pikpak_client.offline_download(url, parent_id=parent_id, name=name)
    except (PikpakAccessTokenExpireException, PikpakException) as e:
        logger.warning(e)
        await refresh_access_token()
        return await offline_download(url)
    except Exception as e:
        msg = f"PikPak Offline Download Error: {e}"
        logger.error(msg)
        raise Exception(msg)


async def pikpak_offline_download(rss: Rss, url: str) -> dict:
    """
    Offline download
    下载到 config.pikpak_download_path/rss.name
    """
    logger.info(f"Offline download {url} to {config.pikpak_download_path}/{rss.name}")
    return await offline_download(url, path=f"{config.pikpak_download_path}/{rss.name}")
