from typing import Any, Dict, List, Optional

from nonebot.log import logger
from pikpakapi.async_api import PikPakApiAsync
from pikpakapi.PikpakException import PikpakAccessTokenExpireException, PikpakException

from .config import config

pikpak_client = PikPakApiAsync(
    username=config.pikpak_username,
    password=config.pikpak_password,
)


async def refresh_access_token() -> None:
    """
    Login or Refresh access_token PikPak

    """
    try:
        await pikpak_client.refresh_access_token()
    except (PikpakException, PikpakAccessTokenExpireException) as e:
        logger.warning(f"refresh_access_token {e}")
        await pikpak_client.login()


async def login() -> None:
    if not pikpak_client.access_token:
        await pikpak_client.login()


async def path_to_id(
    path: Optional[str] = None, create: bool = False
) -> List[Dict[str, Any]]:
    """
    path: str like "/1/2/3"
    create: bool create path if not exist
    将形如 /path/a/b 的路径转换为 文件夹的id
    """
    if not path:
        return []
    paths = [p.strip() for p in path.split("/") if len(p) > 0]
    path_ids = []
    count = 0
    next_page_token = None
    parent_id = None
    while count < len(paths):
        data = await pikpak_client.file_list(
            parent_id=parent_id, next_page_token=next_page_token
        )
        if _id := next(
            (
                f.get("id")
                for f in data.get("files", [])
                if f.get("kind", "") == "drive#folder" and f.get("name") == paths[count]
            ),
            "",
        ):
            path_ids.append(
                {
                    "id": _id,
                    "name": paths[count],
                }
            )
            count += 1
            parent_id = _id
        elif data.get("next_page_token"):
            next_page_token = data.get("next_page_token")
        elif create:
            data = await pikpak_client.create_folder(
                name=paths[count], parent_id=parent_id
            )
            _id = data.get("file").get("id")
            path_ids.append(
                {
                    "id": _id,
                    "name": paths[count],
                }
            )
            count += 1
            parent_id = _id
        else:
            break
    return path_ids


async def pikpak_offline_download(
    url: str,
    path: Optional[str] = None,
    parent_id: Optional[str] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Offline download
    当有path时, 表示下载到指定的文件夹, 否则下载到根目录
    如果存在 parent_id, 以 parent_id 为准
    """
    await login()
    try:
        if not parent_id:
            path_ids = await path_to_id(path, create=True)
            if path_ids and len(path_ids) > 0:
                parent_id = path_ids[-1].get("id")
        return await pikpak_client.offline_download(url, parent_id=parent_id, name=name)
    except (PikpakAccessTokenExpireException, PikpakException) as e:
        logger.warning(e)
        await refresh_access_token()
        return await pikpak_offline_download(
            url=url, path=path, parent_id=parent_id, name=name
        )
    except Exception as e:
        msg = f"PikPak Offline Download Error: {e}"
        logger.error(msg)
        raise Exception(msg) from e
