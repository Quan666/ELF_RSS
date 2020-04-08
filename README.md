# ELF_RSS

**原文地址 [ELF_RSS 订阅插件使用、安装教程](https://myelf.club/index.php/archives/221/ "ELF_RSS 订阅插件使用、安装教程")**
## 前言
rss订阅插件始终没找到个合适自己的，就自己写了一个。
可以实现推特（twitter）转发、YouTube转发、B站直播提醒、Pixiv每日排行榜推送等等功能
## 功能介绍
**管理员qq发送信息到机器人进行添加、删除、修改、查询订阅**

短链接生成

支持多种订阅源，主要兼容RSSHub生成的订阅源

完美兼容酷Q Pro，理论上兼容酷Q Air，但会无法发送图片。

## 使用介绍
非私聊情况下需要在命令前加上机器人昵称，如ELF
### 添加订阅
向机器人发送 
```python
add mytwitter /twitter/user/Huagequan 123456,23445 -1 5 1 0

# 以下为注释

# add是添加订阅命令，若单独发送了add后，根据提示填写订阅信息即可，无需再加add

# mytwitt 为订阅名

# /twitter/user/Huagequan 为订阅地址，此处为rsshub路由地址，非rsshub订阅源要写完整
# 如 https://myelf.club/index.php/feed/ 同时要设置第三方为1

# 123456,23445为订阅者qq号，逗号分开，-1表示设为空

# -1 为订阅群号，和qq号一样英文逗号分开，-1表示为空。
# qq号，群号两者必须有一个不为空，且有效，否则会出错。

# 5 为检查更新的频率，单位分钟/次，最小一分钟，还受到订阅源缓存影响 可选，默认为5

# 1 是否开启代理，有两种参数0/1 1开启，0关闭，设置此项为一必须设置好代理，此项可选，默认为0不开启

# 0 是否第三方订阅，即非rsshub订阅源时必须设为1  可选，默认为0关闭
```
机器人回复成功则添加成功。

### 查看订阅
向机器人发送
`show_all`
即可查看所有订阅

向机器人发送
`show test`
即可查看某一个订阅详细信息
test为订阅名或者订阅链接

### 删除订阅
向机器人发送
`deldy test`
即可删除某一个订阅
test为订阅名或者订阅链接

### 修改订阅

向机器人发送
`change`
即可查看修改方法
```python
输入要修改的订阅的 
订阅名 修改项=,属性 
如:
test dyqq=,xx dsf=0
对应参数： 订阅地址-url，订阅QQ-dyqq，订阅群-dyqun，更新频率-uptime，代理-proxy，第三方-dsf

注：
代理、第三方属性值为1/0
qq、群号前加英文逗号表示追加
```
test为订阅名
也可直接在change后面加修改参数，也可单独修改某一个参数

### 短链接
发送 `短链 https://myelf.club` 即可获得短链接

## 安装
### 要求
1. python3.6+
2. 酷Q

### 开始安装
1. 安装有关依赖

```python
pip install requests
pip install nonebot
pip install feedparser
pip install "nonebot[scheduler]"

# 若有遗漏自己使用pip install xx 的格式安装
# 如果pip安装不了，将pip换成pip3再全部重新安装
# 建议使用pip3
```

2. 下载插件文件
[ELF_RSS 项目地址](https://github.com/Quan666/ELF_RSS "ELF_RSS 项目地址")

3. 修改配置文件
解压打开后修改`config.py` 文件，以记事本打开就行

```python
from nonebot.default_config import *

HOST = '0.0.0.0'
PORT = 8080

NICKNAME = {'ELF', 'elf'}

COMMAND_START = {'', '/', '!', '／', '！'}

SUPERUSERS = {123456789} # 管理员（你）的QQ号

API_ROOT = 'http://127.0.0.1:5700'     #
RSS_PROXY = '127.0.0.1:7890'    # 代理地址
ROOTUSER=123456789    # 主人qq
DEBUG = False
RSSHUB='https://rsshub.app'     # rsshub订阅地址
DELCACHE=3     #缓存删除间隔 天

```

**修改完后记得保存**

### 配置 CQHTTP 插件
单纯运行 NoneBot 实例并不会产生任何效果，因为此刻 酷Q 这边还不知道 NoneBot 的存在，也就无法把消息发送给它，因此现在需要对 CQHTTP 插件做一个简单的配置来让它把消息等事件上报给 NoneBot。

如果你在之前已经按照 安装 的建议使用默认配置运行了一次 CQHTTP 插件，此时 酷Q 的 `data/app/io.github.richardchien.coolqhttpapi/config/` 目录中应该已经有了一个名为 `<user-id>.json` 的文件（`<user-id>` 为你登录的 QQ 账号）。修改这个文件，修改如下配置项（如果不存在相应字段则添加）：
```bash
{
    "ws_reverse_url": "ws://127.0.0.1:8080/ws/",
    "use_ws_reverse": true,
    "enable_heartbeat": true
}
```
**提示**
这里的 `127.0.0.1:8080` 对应 `nonebot.run()` 中传入的 host 和 port，如果在 `nonebot.run()` 中传入的 host 是 0.0.0.0，则插件的配置中需使用任意一个能够访问到 NoneBot 所在环境的 IP，不要直接填 0.0.0.0。特别地，如果你的 酷Q 运行在 Docker 容器中，NoneBot 运行在宿主机中，则默认情况下这里需使用 `172.17.0.1`（即宿主机在 Docker 默认网桥上的 IP，不同机器有可能不同，如果是 macOS 系统或者 Windows 系统，可以考虑使用 host.docker.internal，具体解释详见 Docker 文档的 [Use cases and workarounds](https://docs.docker.com/docker-for-mac/networking/#use-cases-and-workarounds "Use cases and workarounds") 的「I WANT TO CONNECT FROM A CONTAINER TO A SERVICE ON THE HOST」小标题）。

如果你的 CQHTTP 插件版本低于 v4.14.0，还需要删除配置文件中已有的 ws_reverse_api_url 和 ws_reverse_event_url 两项。

**修改之后，在 酷Q 的应用菜单中重启 CQHTTP 插件，或直接重载应用，以使新的配置文件生效。**

### 运行插件
shift+右键打开powershell或命令行输入
```bash
python bot.py

# 或者 python3 bot.py
```
运行后qq会收到消息
**第一次运行要先添加订阅**

**不要关闭窗口**
**CTRL+C可以结束运行**
**如果某次运行无法使用命令，请多次按CTRL+C**


## 相关

[ELF_RSS 项目地址](https://github.com/Quan666/ELF_RSS "ELF_RSS 项目地址")

**感谢以下项目，不分先后**
[RSSHub](https://github.com/DIYgod/RSSHub "RSSHub项目地址")
[NoneBot](https://github.com/richardchien/nonebot "NoneBot")
酷Q

## 推荐文章

[RSShub 搭建教程](https://myelf.club/index.php/archives/192/ "RSShub 搭建教程")
[酷Q机器人搜图插件CQ-picfinder-robot 的部署](https://myelf.club/index.php/archives/186/ "酷Q机器人搜图插件CQ-picfinder-robot 的部署")
[酷Q RSS订阅转发插件rsshub2qq 安装教程](https://myelf.club/index.php/archives/175/ "酷Q RSS订阅转发插件rsshub2qq 安装教程")
