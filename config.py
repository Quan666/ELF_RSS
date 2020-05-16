from nonebot.default_config import *

HOST = '0.0.0.0'
PORT = 8080

NICKNAME = {'ELF', 'elf'}

COMMAND_START = {'', '/', '!', '／', '！'}

SUPERUSERS = {123456789} # 管理员（你）的QQ号

API_ROOT = 'http://127.0.0.1:5700'     #
RSS_PROXY = '127.0.0.1:7890'    # 代理地址
ROOTUSER=[123456]    # 管理员qq,支持多管理员，逗号分隔 如 [1,2,3] 注意，启动消息只发送给第一个管理员
DEBUG = False
RSSHUB='https://rsshub.app'     # rsshub订阅地址
RSSHUB_backup=[] # 备用rsshub地址 填写示例 ['https://rsshub.app','https://rsshub.app']
DELCACHE=3     #缓存删除间隔 天
LIMT=50 # 缓存rss条数

# 解决pixiv.cat无法访问问题
CLOSE_PIXIV_CAT=False #是否关闭使用 pixiv.cat，关闭后必须启用代理
# 以下两项在关闭使用 pixiv.cat时有效，如果你有自己反代pixiv，填上你自己的反代服务器地址即可，没有不要填
PIXIV_REFERER='http://www.pixiv.net' # 请求头 referer 设置
PIXIV_PROXY='i.pximg.net' # 反代图片服务器地址
# 此处推荐一个反代网站 http://pixivic.com   original.img.cheerfun.dev

IsAir=False # 如果你是 酷Q Air 请打开此选项

IsLinux=False # 如果你是Linux部署的，即使用了 docker 部署，请打开此项并设置 Linux_Path
Linux_Path='' # 部署环境为Linux时 wine下插件存放目录 如 Z:\\home\\user\\coolq\\ELF_RSS\\  需要以“\\”结尾 注意路径的“/” 需要换成“\\”
# Linux_Path 的值一定得是 wine下的路径！！！


# MYELF博客地址 https://myelf.club
# 出现问题请在 GitHub 上提 issues
# 项目地址 https://github.com/Quan666/ELF_RSS
# v1.2.6