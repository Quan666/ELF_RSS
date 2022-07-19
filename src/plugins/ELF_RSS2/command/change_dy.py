import re
from typing import Any, List, Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_guild_patch import GuildMessageEvent

from .. import my_trigger as tr
from ..config import DATA_PATH
from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss

RSS_CHANGE = on_command(
    "change",
    aliases={"修改订阅", "modify"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSS_CHANGE.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    if args.extract_plain_text():
        matcher.set_arg("RSS_CHANGE", args)


# 处理带多个值的订阅参数
def handle_property(value: str, property_list: List[Any]) -> List[Any]:
    # 清空
    if value == "-1":
        return []
    value_list = value.split(",")
    # 追加
    if value_list[0] == "":
        value_list.pop(0)
        return property_list + [i for i in value_list if i not in property_list]
    # 防止用户输入重复参数,去重并保持原来的顺序
    return list(dict.fromkeys(value_list))


attribute_dict = {
    "name": "name",
    "url": "url",
    "qq": "user_id",
    "qun": "group_id",
    "channel": "guild_channel_id",
    "time": "time",
    "proxy": "img_proxy",
    "tl": "translation",
    "ot": "only_title",
    "op": "only_pic",
    "ohp": "only_has_pic",
    "upgroup": "is_open_upload_group",
    "downopen": "down_torrent",
    "downkey": "down_torrent_keyword",
    "wkey": "down_torrent_keyword",
    "blackkey": "black_keyword",
    "bkey": "black_keyword",
    "mode": "duplicate_filter_mode",
    "img_num": "max_image_number",
    "stop": "stop",
    "pikpak": "pikpak_offline",
    "ppk": "pikpak_path_key",
}


# 处理要修改的订阅参数
def handle_change_list(
    rss: Rss,
    key_to_change: str,
    value_to_change: str,
    group_id: Optional[int],
    guild_channel_id: Optional[str],
) -> None:
    if key_to_change == "name":
        tr.delete_job(rss)
        rss.rename_file(str(DATA_PATH / f"{Rss.handle_name(value_to_change)}.json"))
    elif (
        key_to_change in {"qq", "qun", "channel"}
        and not group_id
        and not guild_channel_id
    ) or key_to_change == "mode":
        value_to_change = handle_property(
            value_to_change, getattr(rss, attribute_dict[key_to_change])
        )  # type:ignore
    elif key_to_change == "time":
        if not re.search(r"[_*/,-]", value_to_change):
            if int(float(value_to_change)) < 1:
                value_to_change = "1"
            else:
                value_to_change = str(int(float(value_to_change)))
    elif key_to_change in {
        "proxy",
        "tl",
        "ot",
        "op",
        "ohp",
        "upgroup",
        "downopen",
        "stop",
        "pikpak",
    }:
        value_to_change = bool(int(value_to_change))  # type:ignore
        if key_to_change == "stop" and not value_to_change and rss.error_count > 0:
            rss.error_count = 0
    elif (
        key_to_change in {"downkey", "wkey", "blackkey", "bkey", "ppk"}
        and len(value_to_change.strip()) == 0
    ):
        value_to_change = None  # type:ignore
    elif key_to_change == "img_num":
        value_to_change = int(value_to_change)  # type:ignore
    setattr(rss, attribute_dict.get(key_to_change), value_to_change)  # type:ignore


prompt = """\
请输入要修改的订阅
    订阅名[,订阅名,...] 属性=值[ 属性=值 ...]
如:
    test1[,test2,...] qq=,123,234 qun=-1
对应参数:
    订阅名(-name): 禁止将多个订阅批量改名，名称相同会冲突
    订阅链接(-url)
    QQ(-qq) 
    群(-qun)
    更新频率(-time)
    代理(-proxy) 
    翻译(-tl)
    仅Title(ot)
    仅图片(-op)
    仅含图片(-ohp)
    下载种子(-downopen)
    白名单关键词(-wkey)
    黑名单关键词(-bkey)
    种子上传到群(-upgroup)
    去重模式(-mode)
    图片数量限制(-img_num): 只发送限定数量的图片，防止刷屏
    正文移除内容(-rm_list): 从正文中移除指定内容，支持正则
    停止更新(-stop): 停止更新订阅
    PikPak离线(-pikpak): 开启PikPak离线下载
    PikPak离线路径匹配(-ppk): 匹配离线下载的文件夹,设置该值后生效
注：
    1. 仅含有图片不同于仅图片，除了图片还会发送正文中的其他文本信息
    2. proxy/tl/ot/op/ohp/downopen/upgroup/stop/pikpak 值为 1/0
    3. 去重模式分为按链接(link)、标题(title)、图片(image)判断，其中 image 模式生效对象限定为只带 1 张图片的消息。如果属性中带有 or 说明判断逻辑是任一匹配即去重，默认为全匹配
    4. 白名单关键词支持正则表达式，匹配时推送消息及下载，设为空(wkey=)时不生效
    5. 黑名单关键词同白名单相似，匹配时不推送，两者可以一起用
    6. 正文待移除内容格式必须如：rm_list='a' 或 rm_list='a','b'。该处理过程在解析 html 标签后进行，设为空使用 rm_list='-1'"
    7. QQ、群号、去重模式前加英文逗号表示追加，-1设为空
    8. 各个属性使用空格分割
详细用法请查阅文档。\
"""


@RSS_CHANGE.got("RSS_CHANGE", prompt=prompt)
async def handle_rss_change(
    event: MessageEvent, change_info: str = ArgPlainText("RSS_CHANGE")
) -> None:
    group_id = event.group_id if isinstance(event, GroupMessageEvent) else None
    guild_channel_id = (
        f"{event.guild_id}@{event.channel_id}"
        if isinstance(event, GuildMessageEvent)
        else None
    )
    name_list = change_info.split(" ")[0].split(",")
    rss_list: List[Rss] = []
    for name in name_list:
        if rss_tmp := Rss.get_one_by_name(name=name):
            rss_list.append(rss_tmp)

    # 出于公平考虑，限制订阅者只有当前群组或频道时才能修改订阅，否则只有超级管理员能修改
    if group_id:
        if re.search(" (qq|qun|channel)=", change_info):
            await RSS_CHANGE.finish("❌ 禁止在群组中修改订阅账号！如要取消订阅请使用 deldy 命令！")
        rss_list = [
            rss
            for rss in rss_list
            if rss.group_id == [str(group_id)]
            and not rss.user_id
            and not rss.guild_channel_id
        ]

    if guild_channel_id:
        if re.search(" (qq|qun|channel)=", change_info):
            await RSS_CHANGE.finish("❌ 禁止在子频道中修改订阅账号！如要取消订阅请使用 deldy 命令！")
        rss_list = [
            rss
            for rss in rss_list
            if rss.guild_channel_id == [str(guild_channel_id)]
            and not rss.user_id
            and not rss.guild_channel_id
        ]

    if not rss_list:
        await RSS_CHANGE.finish("❌ 请检查是否存在以下问题：\n1.要修改的订阅名不存在对应的记录\n2.当前群组或频道无权操作")
    elif len(rss_list) > 1 and " name=" in change_info:
        await RSS_CHANGE.finish("❌ 禁止将多个订阅批量改名！会因为名称相同起冲突！")

    # 参数特殊处理：正文待移除内容
    change_list = handle_rm_list(rss_list, change_info)

    separator = "\n----------------------\n"
    rss_msg_list = await batch_change_rss(
        change_list, group_id, guild_channel_id, rss_list
    )
    result_msg = (
        f"修改了 {len(rss_msg_list)} 条订阅：{separator}{separator.join(rss_msg_list)}"
    )
    await RSS_CHANGE.finish(f"👏 修改成功\n{result_msg}")


async def batch_change_rss(
    change_list: List[str],
    group_id: Optional[int],
    guild_channel_id: Optional[str],
    rss_list: List[Rss],
) -> List[str]:
    rss_msg_list = []
    for rss in rss_list:
        rss_name = rss.name
        for change_dict in change_list:
            key_to_change, value_to_change = change_dict.split("=", 1)
            if key_to_change in attribute_dict.keys():
                # 对用户输入的去重模式参数进行校验
                mode_property_set = {"", "-1", "link", "title", "image", "or"}
                if key_to_change == "mode" and (
                    set(value_to_change.split(",")) - mode_property_set
                    or value_to_change == "or"
                ):
                    await RSS_CHANGE.finish(f"❌ 去重模式参数错误！\n{change_dict}")
                handle_change_list(
                    rss, key_to_change, value_to_change, group_id, guild_channel_id
                )
            else:
                await RSS_CHANGE.finish(f"❌ 参数错误！\n{change_dict}")

        # 参数解析完毕，写入
        rss.upsert(rss_name)

        # 加入定时任务
        if not rss.stop:
            await tr.add_job(rss)
        else:
            tr.delete_job(rss)
            logger.info(f"{rss_name} 已停止更新")

        # 隐私考虑，不展示除当前群组或频道外的群组、频道和QQ
        rss_msg = str(rss.hide_some_infos(group_id, guild_channel_id))
        rss_msg_list.append(rss_msg)
    return rss_msg_list


# 参数特殊处理：正文待移除内容
def handle_rm_list(rss_list: List[Rss], change_info: str) -> List[str]:
    rm_list_exist = re.search(" rm_list='.+'", change_info)
    rm_list = None

    if rm_list_exist:
        rm_list_str = rm_list_exist[0].lstrip().replace("rm_list=", "")
        rm_list = [i.strip("'") for i in rm_list_str.split("','")]
        change_info = change_info.replace(rm_list_exist[0], "")

    if rm_list:
        for rss in rss_list:
            if len(rm_list) == 1 and rm_list[0] == "-1":
                setattr(rss, "content_to_remove", None)
            else:
                setattr(rss, "content_to_remove", rm_list)

    change_list = change_info.split(" ")
    # 去掉订阅名
    change_list.pop(0)

    return change_list
