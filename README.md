# ELF_RSS

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/b799d894ed354d5999fb6047543c494c)](https://www.codacy.com/gh/Quan666/ELF_RSS/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Quan666/ELF_RSS&amp;utm_campaign=Badge_Grade)
[![QQ Group](https://img.shields.io/badge/qq%E7%BE%A4-984827132-orange?style=flat-square)](https://jq.qq.com/?_wv=1027&k=sST08Nkd)

> 1. 容易使用的命令
> 2. 更规范的代码，方便移植到你自己的机器人
> 3. 使用全新的 [Nonebot2](https://v2.nonebot.dev/guide/) 框架

这是一个以 Python 编写的 QQ 机器人插件，用于订阅 RSS 并实时以 QQ消息推送。

算是第一次用 Python 写出来的比较完整、实用的项目。代码比较难看，正在重构中

---

当然也有很多插件能够做到订阅 RSS ，但不同的是，大多数都需要在服务器上修改相应配置才能添加订阅，而该插件只需要发送QQ消息给机器人就能动态添加订阅。

对于订阅，支持QQ、QQ群、QQ频道的单个、多个订阅。

每个订阅的个性化设置丰富，能够应付多种场景。

## 功能介绍

* 发送命令添加、删除、查询、修改 RSS 订阅
* 交互式添加 RSSHub 订阅
* 订阅内容翻译（使用谷歌机翻，可设置为百度翻译）
* 个性化订阅设置（更新频率、翻译、仅标题、仅图片等）
* 多平台支持
* 图片压缩后发送
* 种子下载并上传到群文件
* 消息支持根据链接、标题、图片去重
* 可设置只发送限定数量的图片，防止刷屏
* 可设置从正文中要移除的指定内容，支持正则

## 文档目录

> 注意：推荐 Python 3.8.3+ 版本 Windows版安装包下载地址：[https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe](https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe)
>
> * [部署教程](docs/部署教程.md)
> * [使用教程](docs/2.0%20使用教程.md)
> * [使用教程 旧版](docs/1.0%20使用教程.md)
> * [常见问题](docs/常见问题.md)
> * [更新日志](docs/更新日志.md)

## 效果预览

![image-20201221163514747](https://cdn.jsdelivr.net/gh/Quan666/CDN/pic/image-20201221163514747.png)

![image-20201221163555086](https://cdn.jsdelivr.net/gh/Quan666/CDN/pic/image-20201221163555086.png)

![image-20201221163721358](https://cdn.jsdelivr.net/gh/Quan666/CDN/pic/image-20201221163721358.png)

![image](https://user-images.githubusercontent.com/32663291/117431780-3373a100-af5c-11eb-9de2-ff75948abf1c.png)

## TODO

* [x] 1. 订阅信息保护，不在群组中输出订阅QQ、群组
* [x] 2. 更为强大的检查更新时间设置
* [x] 3. RSS 源中 torrent 自动下载并上传至订阅群（适合番剧订阅）
* [ ] 4. 暂停检查订阅更新
* [ ] 5. 模糊匹配订阅名
* [ ] 6. 性能优化，全部替换为异步操作

## 感谢以下项目或服务

不分先后

* [RSSHub](https://github.com/DIYgod/RSSHub)
* [Nonebot](https://github.com/nonebot/nonebot2)
* [酷Q（R. I. P）](https://cqp.cc/)
* [coolq-http-api](https://github.com/richardchien/coolq-http-api)
* [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

## Star History

[![Star History](https://starchart.cc/Quan666/ELF_RSS.svg)](https://starchart.cc/Quan666/ELF_RSS)
