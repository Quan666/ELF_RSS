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
DELCACHE=3     #缓存删除间隔 天
LIMT=50 # 缓存rss条数

# MYELF博客地址 https://myelf.club
# 出现问题请在 GitHub 上提 issues
# 项目地址 https://github.com/Quan666/ELF_RSS
# v1.2.2