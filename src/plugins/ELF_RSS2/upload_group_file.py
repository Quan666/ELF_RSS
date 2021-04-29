import nonebot
from nonebot import on_command, logger
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me
from qbittorrent import Client
from .config import config
upload_group_file = on_command('uploadfile', rule=to_me(), priority=5)


async def get_qb():
    try:
        qb = Client(config.qb_web_url)
        qb.login()
    except BaseException as e:
        msg = '❌ 无法连接到 qbittorrent ,请检查：\n1.是否启动程序\n2.是否勾选了“Web用户界面（远程控制）”\n3.连接地址、端口是否正确\nE: {}'.format(e)
        logger.error(msg)
        await upload_group_file.send(msg)
        return None
    try:
        qb.get_default_save_path()
    except BaseException as e:
        msg = '❌ 无法连登录到 qbittorrent ,请检查是否勾选 “对本地主机上的客户端跳过身份验证”。\nE: {}'.format(
            e)
        logger.error(msg)
        await upload_group_file.send(msg)
        return None
    return qb


def getSize(size: int) -> str:
    kb = 1024
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024

    if size >= tb:
        return "%.2f TB" % float(size / tb)
    if size >= gb:
        return "%.2f GB" % float(size / gb)
    if size >= mb:
        return "%.2f MB" % float(size / mb)
    if size >= kb:
        return "%.2f KB" % float(size / kb)


# 检查下载状态
async def check_down_status(hash: str, group_id: int):
    qb = await get_qb()
    if not qb:
        return
    info = qb.get_torrent(hash)
    files = qb.get_torrent_files(hash)
    bot, = nonebot.get_bots().values()
    if info['total_downloaded'] - info['total_size'] >= 0.000000:
        for tmp in files:
            # 异常包起来防止超时报错导致后续不执行
            try:
                if config.qb_down_path and len(config.qb_down_path) > 0:
                    path = config.qb_down_path + tmp['name']
                else:
                    path = info['save_path'] + tmp['name']
                await upload_group_file.send(str('{}\n大小：{}\nHash: {} \n开始上传'.format(tmp['name'], getSize(info['total_size']), hash)))
                await bot.call_api('upload_group_file', group_id=group_id, file=path, name=tmp['name'])
            except Exception:
                continue
    else:
        await upload_group_file.send(str('Hash: {} \n下载了 {}%\n平均下载速度：{} KB/s'.format(hash, round(
            info['total_downloaded'] / info['total_size'] * 100, 2), round(info['dl_speed_avg'] / 1024, 2))))


@upload_group_file.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    hash = str(event.__getattribute__('message'))
    if event.__getattribute__('message_type') == 'private':
        await upload_group_file.finish('请在群聊中使用哦')
    await check_down_status(hash=hash, group_id=event.group_id)
