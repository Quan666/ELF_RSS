# coding: utf8

"""
    @Author: LCY
    @Contact: lchuanyong@126.com
    @blog: http://http://blog.csdn.net/lcyong_
    @Date: 2018-01-15
    @Time: 19:19
    说明： appid和secretKey为百度翻译文档中自带的，需要切换为自己的
           python2和python3部分库名称更改对应如下：
           httplib      ---->    http.client
           md5          ---->    hashlib.md5
           urllib.quote ---->    urllib.parse.quote
    官方链接：
           http://api.fanyi.baidu.com/api/trans/product/index

"""

import hashlib
import http.client
import json
import random
import urllib

from nonebot import logger

from ..config import config


def baidu_translate(content):
    appid = config.baidu_id
    secret_key = config.baidu_key
    http_client = None
    my_url = "/api/trans/vip/translate"
    q = content
    from_lang = "auto"  # 源语言
    to_lang = "zh"  # 翻译后的语言
    salt = random.randint(32768, 65536)
    sign = str(appid) + str(q) + str(salt) + str(secret_key)
    sign = hashlib.md5(sign.encode()).hexdigest()
    my_url = (
        my_url
        + "?appid="
        + str(appid)
        + "&q="
        + urllib.parse.quote(q)
        + "&from="
        + from_lang
        + "&to="
        + to_lang
        + "&salt="
        + str(salt)
        + "&sign="
        + sign
    )

    try:
        http_client = http.client.HTTPConnection("api.fanyi.baidu.com")
        http_client.request("GET", my_url)
        # response是HTTPResponse对象
        response = http_client.getresponse()
        json_response = response.read().decode("utf-8")  # 获得返回的结果，结果为json格式
        js = json.loads(json_response)  # 将json格式的结果转换字典结构
        dst = str(js["trans_result"][0]["dst"])  # 取得翻译后的文本结果
        return dst  # 打印结果
    except Exception as e:
        logger.error(e)
        return f"翻译失败：{e}"
    finally:
        if http_client:
            http_client.close()


if __name__ == "__main__":
    while True:
        print("请输入要翻译的内容，要退出请输入q")
        input_content = input()
        if input_content == "q":
            break
        baidu_translate(input_content)
