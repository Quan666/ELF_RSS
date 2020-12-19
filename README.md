# ELF_RSS

## 2.0 特性介绍

1. 使用全新 [Nonebot2](https://v2.nonebot.dev/guide/) 框架
2. 支持热重载
3. 性能优化
4. 代码结构优化
注意：1.x 仍然可以使用

## 效果预览
![](https://cdn.jsdelivr.net/gh/Quan666/CDN@master/pic/elfrss_1.png)
![](https://cdn.jsdelivr.net/gh/Quan666/CDN@master/pic/elfrss_2.png)
![](https://cdn.jsdelivr.net/gh/Quan666/CDN@master/pic/elfrss_3.png)

## 如何使用

>  **注意： 需要 Python 3.7+**


### 一 、配置 QQ 协议端

   目前支持的协议有:

   - [OneBot(CQHTTP)](https://github.com/howmanybots/onebot/blob/master/README.md)

   QQ 协议端举例:

   - [go-cqhttp ](https://github.com/Mrs4s/go-cqhttp)(基于 [MiraiGo ](https://github.com/Mrs4s/MiraiGo))
   - [cqhttp-mirai-embedded](https://github.com/yyuueexxiinngg/cqhttp-mirai/tree/embedded)
   - [Mirai ](https://github.com/mamoe/mirai)+ [cqhttp-mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)
   - [Mirai ](https://github.com/mamoe/mirai)+ [Mirai Native ](https://github.com/iTXTech/mirai-native)+ [CQHTTP](https://github.com/richardchien/coolq-http-api)
   - [OICQ-http-api ](https://github.com/takayama-lily/onebot)(基于 [OICQ](https://github.com/takayama-lily/oicq))

   这里以 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)为例

   1. 下载 go-cqhttp 对应平台的 release 文件，[点此前往](https://github.com/Mrs4s/go-cqhttp/releases)

   2. 运行 exe 文件或者使用 `./go-cqhttp` 启动

   3. 生成默认配置文件并修改默认配置

      ```json
      {
        "uin": 你的QQ号,
        "password": "你的密码",
        "encrypt_password": false,
        "password_encrypted": "",
        "enable_db": true,
        "access_token": "",
        "relogin": {
          "enabled": true,
          "relogin_delay": 3,
          "max_relogin_times": 0
        },
        "_rate_limit": {
          "enabled": false,
          "frequency": 0,
          "bucket_size": 0
        },
        "ignore_invalid_cqcode": false,
        "force_fragmented": true,
        "heartbeat_interval": 0,
        "http_config": {
          "enabled": false,
          "host": "0.0.0.0",
          "port": 5700,
          "timeout": 0,
          "post_urls": {}
        },
        "ws_config": {
          "enabled": false,
          "host": "0.0.0.0",
          "port": 6700
        },
        "ws_reverse_servers": [
          {
            "enabled": true,
            "reverse_url": "ws://127.0.0.1:8080/cqhttp/ws",
            "reverse_api_url": "",
            "reverse_event_url": "",
            "reverse_reconnect_interval": 3000
          }
        ],
        "post_message_format": "array",
        "use_sso_address": false,
        "debug": false,
        "log_level": "",
        "web_ui": {
          "enabled": true,
          "host": "0.0.0.0",
          "web_ui_port": 9999,
          "web_input": false
        }
      }
      ```

      其中 `ws://127.0.0.1:8080/cqhttp/ws` 中的 `127.0.0.1` 和 `8080` 应分别对应 nonebot 配置的 HOST 和 PORT

      

      **其中以下配置项务必按照下方样式修改！**

      ```json
      "ws_reverse_servers": [
          {
            "enabled": true,
            "reverse_url": "ws://127.0.0.1:8080/cqhttp/ws",
            "reverse_api_url": "",
            "reverse_event_url": "",
            "reverse_reconnect_interval": 3000
          }
        ],
      ```

      4. 再次运行 exe 文件或者使用 `./go-cqhttp` 启动

### 二、配置ELF_RSS

#### 第一次部署

1. 下载代码到本地

2. 运行 `pip install -r requirements.txt` 

3. 修改插件配置 （文件 `.env` ）

   > **注意：请将 `ENVIRONMENT=dev` 的值 `env` 删除**
   >
   > 请按照 注释 修改配置文件

   ```bash
   ENVIRONMENT=dev
   HOST=0.0.0.0  # 配置 NoneBot 监听的 IP/主机名
   PORT=8080  # 配置 NoneBot 监听的端口
   DEBUG=false  # 开启 debug 模式 **请勿在生产环境开启**
   SUPERUSERS=["123123123"]  # 配置 NoneBot 超级用户 # 管理员qq,支持多管理员，逗号分隔 注意，启动消息只发送给第一个管理员
   NICKNAME=["elf", "ELF"]  # 配置机器人的昵称
   COMMAND_START=["","/"]  # 配置命令起始字符
   COMMAND_SEP=["."]  # 配置命令分割字符
   
   # Custom Configs
   RSS_PROXY = '127.0.0.1:7890'  # 代理地址
   RSSHUB = 'https://rsshub.app'  # rsshub订阅地址
   RSSHUB_backup = []  # 备用rsshub地址 填写示例 ['https://rsshub.app','https://rsshub.app']
   DELCACHE = 3  # 缓存删除间隔 天
   LIMT = 50  # 缓存rss条数
   
   #群组订阅的默认参数
   add_uptime = 10    #默认订阅更新时间
   add_proxy = false  #默认是否启用代理
   
   # 图片压缩大小 kb * 1024 = MB
   ZIP_SIZE = 3072
   
   blockquote = true    #是否显示转发的内容(主要是微博)，默认打开，如果关闭还有转发的信息的话，可以自行添加进屏蔽词(但是这整条消息就会没)
   showBlockword = true   #是否显示内含屏蔽词的信息信息，默认打开
   Blockword = ["互动抽奖","微博抽奖平台"]   #屏蔽词填写 支持正则,看里面格式就明白怎么添加了吧(
   
   #使用百度翻译API 可选，填的话两个都要填，不填默认使用谷歌翻译(需墙外？)
   # Baidu Translate API
   UseBaidu = false
   BaiduID = ''
   BaiduKEY = ''
   #百度翻译接口appid和secretKey，前往http://api.fanyi.baidu.com/获取
   #一般来说申请标准版免费就够了，想要好一点可以认证上高级版，有月限额，rss用也足够了
   
   
   # 解决pixiv.cat无法访问问题
   CLOSE_PIXIV_CAT = false  # 是否关闭使用 pixiv.cat，关闭后必须启用代理
   # 以下两项在关闭使用 pixiv.cat时有效，如果你有自己反代pixiv，填上你自己的反代服务器地址即可，没有不要填
   PIXIV_REFERER = 'http://www.pixiv.net'  # 请求头 referer 设置
   PIXIV_PROXY = 'i.pximg.net'  # 反代图片服务器地址
   # 此处推荐一个反代网站 http://pixivic.com   original.img.cheerfun.dev
   
   IsLinux = false  # 如果你是Linux部署的，请开启此项
   
   VERSION="v2.0.0"
   ```



5. 运行 `nb run`
6. 收到机器人发送的启动成功消息

#### 从 Nonebot1 到 NoneBot2

1. 卸载 nonebot1

   ```bash
   pip uninstall nonebot
   ```

2. 运行 

   ```
   pip install -r requirements.txt
   ```

3. 参照 `第一次部署`

#### 已经部署过其它 Nonebot2 机器人

1. 下载 `src/plugins/ELF_RSS2` 文件夹 到你部署好了的机器人 `plugins` 目录
2. 下载 `requirements.txt` 文件，并运行 `pip install -r requirements.txt` 
3. 同 `第一次部署` 一样，修改配置文件
4. 运行 `nb run`
5. 收到机器人发送的启动成功消息

#### docker 部署

1. 待补充

