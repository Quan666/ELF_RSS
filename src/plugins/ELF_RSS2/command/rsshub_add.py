from typing import Any, Dict

import aiohttp
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot_plugin_guild_patch import GuildMessageEvent
from yarl import URL

from ..config import config
from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss
from .add_dy import add_feed

rsshub_routes: Dict[str, Any] = {}


RSSHUB_ADD = on_command(
    "rsshub_add",
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSSHUB_ADD.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    if args.extract_plain_text():
        matcher.set_arg("router", args)


@RSSHUB_ADD.got("name", prompt="请输入要订阅的订阅名")
async def handle_feed_name(name: str = ArgPlainText("name")) -> None:
    if _ := Rss.get_one_by_name(name=name):
        await RSSHUB_ADD.reject(f"已存在名为 {name} 的订阅，请重新输入")


@RSSHUB_ADD.got("router", prompt="请输入要订阅的 RSSHub 路由名")
async def handle_rsshub_routes(
    state: T_State, route: str = ArgPlainText("router")
) -> None:
    rsshub_url = URL(config.rsshub)
    # 对本机部署的 RSSHub 不使用代理
    local_host = [
        "localhost",
        "127.0.0.1",
    ]
    if config.rss_proxy and rsshub_url.host not in local_host:
        proxy = f"http://{config.rss_proxy}"
    else:
        proxy = None

    global rsshub_routes
    if not rsshub_routes:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            resp = await session.get(rsshub_url.with_path("api/routes"), proxy=proxy)
            if resp.status != 200:
                await RSSHUB_ADD.finish("获取路由数据失败，请检查 RSSHub 的地址配置及网络连接")
            rsshub_routes = await resp.json()

    if route not in rsshub_routes["data"]:
        await RSSHUB_ADD.reject("没有这个路由，请重新输入")
    else:
        route_list = rsshub_routes["data"][route]["routes"]
        state["route_list"] = route_list
        if len(route_list) > 1:
            await RSSHUB_ADD.send(
                "请输入序号来选择要订阅的 RSSHub 路由：\n"
                + "\n".join(
                    f"{index + 1}. {__route}"
                    for index, __route in enumerate(route_list)
                )
            )
        else:
            state["route_index"] = Message("0")


@RSSHUB_ADD.got("route_index")
async def handle_route_index(
    state: T_State, route_index: str = ArgPlainText("route_index")
) -> None:
    route = state["route_list"][int(route_index) - 1]
    if args := [i for i in route.split("/") if i.startswith(":")]:
        await RSSHUB_ADD.send(
            '请依次输入要订阅的 RSSHub 路由参数，并用 "/" 分隔：\n'
            + "/".join(
                f"{i.rstrip('?')}(可选)" if i.endswith("?") else f"{i}" for i in args
            )
            + "\n要置空请输入#或直接留空"
        )
    else:
        state["route_args"] = Message()


@RSSHUB_ADD.got("route_args")
async def handle_route_args(
    event: Event,
    state: T_State,
    name: str = ArgPlainText("name"),
    route_index: str = ArgPlainText("route_index"),
    route_args: str = ArgPlainText("route_args"),
) -> None:
    route = state["route_list"][int(route_index) - 1]
    feed_url = "/".join([i for i in route.split("/") if not i.startswith(":")])
    for i in route_args.split("/"):
        if len(i.strip("#")) > 0:
            feed_url += f"/{i}"

    user_id = event.get_user_id()
    group_id = None
    guild_channel_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    elif isinstance(event, GuildMessageEvent):
        guild_channel_id = f"{str(event.guild_id)}@{str(event.channel_id)}"

    rss = Rss()
    rss.name = name
    rss.url = feed_url
    await add_feed(rss, user_id, group_id, guild_channel_id)
