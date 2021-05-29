# 迁移到 go-cqhttp

> **前提：已经按照部署流程部署好 ELF_RSS**

准备工作

- 下载 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp/releases)

## 开始

1. 解压并运行 go-cqhttp.exe 文件，之后会生成一堆文件，关闭软件
2. 如版本使用的是 `v1.0.0-beta2` 及其之后的，因配置文件改为 yaml 格式，直接参考[官方文档](https://github.com/Mrs4s/go-cqhttp/blob/master/docs/config.md)  
    否则，修改 config.json 文件，参考配置如下： 其中 "uin" 是QQ号、password是QQ密码

    ```json
    {
        "uin": 123456789,
        "password": "123456789",
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
            "frequency": 1,
            "bucket_size": 1
        },
        "ignore_invalid_cqcode": false,
        "force_fragmented": true,
        "heartbeat_interval": 0,
        "http_config": {
            "enabled": true,
            "host": "0.0.0.0",
            "port": 5700,
            "timeout": 0,
            "post_urls": {}
        },
        "ws_config": {
            "enabled": true,
            "host": "0.0.0.0",
            "port": 6700
        },
        "ws_reverse_servers": [
            {
                "enabled": true,
                "reverse_url": "ws://127.0.0.1:8080/cqhttp/ws",
                "reverse_api_url": "ws://127.0.0.1:8080/cqhttp/ws/api/",
                "reverse_event_url": "ws://127.0.0.1:8080/cqhttp/ws/event/",
                "reverse_reconnect_interval": 3000
            }
        ],
        "post_message_format": "string",
        "debug": false,
        "log_level": ""
    }
    ```

3. 再次运行 go-cqhttp
4. 到此基本就迁移完毕
