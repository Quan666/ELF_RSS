from nonebot import on_command, CommandSession
import requests

# on_command 装饰器将函数声明为一个命令处理器
# 这里 uri 为命令的名字，同时允许使用别名
@on_command('uri', aliases=('短链', 'url', 'uri','URL','URI'))
async def uri(session: CommandSession):
    # 从会话状态（session.state）中获取链接(url)，如果当前不存在，则询问用户
    url = session.get('url', prompt='发送要想压缩的链接')
    # 获取url
    uri_report = await get_uri_of_url(url)
    # 向用户发送uri
    await session.send(uri_report)


# uri.args_parser 装饰器将函数声明为 uri 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@uri.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将url跟在命令名后面，作为参数传入
            # 例如用户可能发送了：uri https://myelf.club
            session.state['url'] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的url（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('要压缩的链接不能为空呢，请重新输入')

    # 如果当前正在向用户询问更多信息（例如本例中的要压缩的链接），且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg


async def get_uri_of_url(url: str) -> str:
    www = 'https://t.myelf.club/a/?url=' + url
    data_json = requests.get(www).json()
    return ''+data_json['URI']