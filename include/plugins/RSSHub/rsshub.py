# -*- coding: UTF-8 -*-
import feedparser
import json
import codecs
from pyquery import PyQuery as pq
import re
import os.path
import requests
import uuid
import time
from datetime import datetime,timezone,timedelta
import config
import difflib
import logging
from nonebot.log import logger
from . import RSS_class
from googletrans import Translator
import emoji
# 存储目录
file_path = './data/'
#代理
proxy = config.RSS_PROXY
proxies = {
    'http': 'http://' + proxy,
    'https': 'https://' + proxy,
}
status_code=[200,301,302]
def getRSS(rss:RSS_class.rss)->list:# 链接，订阅名
    try:
        # 检查是否存在rss记录
        if os.path.isfile(file_path + rss.name + '.json'):
            d = feedparser.parse(rss.geturl())  # 获取xml
            if d.status not in status_code and not rss.notrsshub and config.RSSHUB_backup:
                logger.error('RSSHub :' + config.RSSHUB + ' 访问失败 ！使用备用RSSHub 地址！')
                for rsshub_url in config.RSSHUB_backup:
                    d = feedparser.parse(rsshub_url + rss.url)  # 获取xml
                    if d.status in status_code:
                        logger.info(rsshub_url + ' 抓取成功！')
                        break;
            if d.status not in status_code :
                logger.error(rss.name + ' 抓取失败，请检查订阅地址是否正常！')
            change = checkUpdate(d, readRss(rss.name))  # 检查更新
            if len(change) > 0:
                writeRss(d, rss.name)  # 写入文件
                msg_list = []
                for item in change:
                    msg = '【' + d.feed.title + '】更新了!\n----------------------\n'

                    if not rss.only_title:
                        # 处理item['summary']只有图片的情况
                        text = re.sub('<video.+?><\/video>|<img.+?>', '', item['summary'])
                        text = re.sub('<br>', '', text)
                        Similarity = difflib.SequenceMatcher(None, text, item['title'])
                        # print(Similarity.quick_ratio())
                        if Similarity.quick_ratio() <= 0.1:  # 标题正文相似度
                            msg = msg + '标题：' + item['title'] + '\n'
                        msg = msg + '内容：' + checkstr(item['summary'], rss.img_proxy, rss.translation) + '\n'
                    else:
                        msg = msg + '标题：' + item['title'] + '\n'

                    msg = msg + '原链接：' + item['link'] + '\n'

                    try:
                        loc_time = time.mktime(item['published_parsed'])
                        msg = msg + '日期：' + time.strftime("%m{}%d{} %H:%M:%S",
                                                          time.localtime(loc_time + 28800.0)).format('月', '日')
                    except BaseException:
                        msg = msg + '日期：' + time.strftime("%m{}%d{} %H:%M:%S", time.localtime()).format('月', '日')
                    # print(msg+'\n\n\n')
                    msg_list.append(msg)
                return msg_list
            else:
                return []
        else:
            d = feedparser.parse(rss.geturl())  # 获取xml
            try:
                if d.status in status_code:
                    writeRss(d, rss.name)  # 写入文件
                else:
                    logger.error('获取 ' + rss.name + ' 订阅xml失败！！！请检查订阅地址是否可用！')
            except  Exception as e:
                logger.error('出现异常，获取 ' + rss.name + ' 订阅xml失败！！！请检查订阅地址是否可用！  E:'+str(e))
            return []
    except Exception as e:
        logger.error(rss.name + ' 抓取失败，请检查订阅地址是否正确！ E:'+str(e))
        return []

# 下载图片
def dowimg(url:str,img_proxy:bool)->str:
    img_path = file_path+'imgs'+ os.sep
    if not os.path.isdir(img_path):
        logger.info(img_path+'文件夹不存在，已重新创建')
        os.makedirs(img_path)  # 创建目录

    file_suffix = os.path.splitext(url)  # 返回列表[路径/文件名，文件后缀]
    name = str(uuid.uuid4())
    try:
        if config.CLOSE_PIXIV_CAT and url.find('pixiv.cat') >= 0:
            img_proxy = False
            headers = {'referer': config.PIXIV_REFERER}
            img_id = re.sub('https://pixiv.cat/', '', url)
            img_id = img_id[:-4]
            info_list = img_id.split('-')
            req_json = requests.get('https://api.imjad.cn/pixiv/v1/?type=illust&id=' + info_list[0]).json()
            if len(info_list) >= 2:
                url = req_json['response'][0]['metadata']['pages'][int(info_list[1]) - 1]['image_urls']['large']
            else:
                url = req_json['response'][0]['image_urls']['large']

            # 使用第三方反代服务器
            url = re.sub('i.pximg.net', config.PIXIV_PROXY, url)

            if img_proxy:
                pic = requests.get(url, timeout=5000, proxies=proxies, headers=headers)
            else:
                pic = requests.get(url, timeout=5000, headers=headers)
        else:
            if img_proxy:
                pic = requests.get(url, timeout=5000, proxies=proxies)
            else:
                pic = requests.get(url, timeout=5000)


        #大小控制，图片压缩
        #print(len(pic.content)/1024)

        if len(file_suffix[1]) > 0:
            filename = name + file_suffix[1]
        elif pic.headers['Content-Type']=='image/jpeg':
            filename=name+'.jpg'
        elif pic.headers['Content-Type']=='image/png':
            filename=name+'.png'
        else:
            filename = name + '.jpg'
        with codecs.open(img_path + filename, "wb") as dump_f:
            dump_f.write(pic.content)
        if config.IsLinux:
            return filename
        else:
            imgs_name = img_path + filename
            if len(imgs_name) > 0:
                imgs_name = os.getcwd() + re.sub('\./', r'\\', imgs_name)
                imgs_name = re.sub(r'\\', r'\\\\', imgs_name)
                imgs_name = re.sub(r'/', r'\\\\', imgs_name)
            return imgs_name
    except requests.exceptions.ConnectionError as e:
        logger.error('图片下载失败 E:'+str(e))
        return ''


#处理正文
def checkstr(rss_str:str,img_proxy:bool,translation:bool)->str:

    # 去掉换行
    rss_str = re.sub('\n', '', rss_str)

    doc_rss = pq(rss_str)
    rss_str = str(doc_rss)

    # 处理一些标签
    rss_str = re.sub('<br/><br/>|<br><br>|<br>|<br/>', '\n', rss_str)
    rss_str = re.sub('<span>|</span>', '', rss_str)
    rss_str = re.sub('<pre.+?\">|</pre>', '', rss_str)
    rss_str = re.sub('<p>|</p>|<b>|</b>', '', rss_str)
    rss_str = re.sub('<div>|</div>|<strong>|</strong>', '', rss_str)

    rss_str_tl = rss_str # 翻译用副本
    # <a> 标签处理
    doc_a = doc_rss('a')
    a_str = ''
    for a in doc_a.items():
        if str(a.text()) != a.attr("href"):
            rss_str = re.sub(re.escape(str(a)), str(a.text()) + ':' + (a.attr("href")) + '\n', rss_str)
        else:
            rss_str = re.sub(re.escape(str(a)), (a.attr("href")) + '\n', rss_str)
        rss_str_tl = re.sub(re.escape(str(a)), '', rss_str_tl)


    # 处理图片
    doc_img = doc_rss('img')
    for img in doc_img.items():
        rss_str_tl = re.sub(re.escape(str(img)), '', rss_str_tl)
        img_path = dowimg(img.attr("src"), img_proxy)
        if not config.IsAir:
            if len(img_path) > 0:
                if config.IsLinux:
                    rss_str = re.sub(re.escape(str(img)),
                                     r'[CQ:image,file=file:///' + re.escape(config.Linux_Path)+re.escape('data\\imgs\\') + str(
                                         img_path) + ']',
                                     rss_str)
                else:
                    rss_str = re.sub(re.escape(str(img)), r'[CQ:image,file=file:///' + str(img_path) + ']', rss_str)
            else:
                rss_str = re.sub(re.escape(str(img)), r'\n图片走丢啦！\n', rss_str, re.S)
        else:
            rss_str = re.sub(re.escape(str(img)), r'图片链接：' + img.attr("src") + '\n', rss_str, re.S)

    # 处理视频
    doc_video = doc_rss('video')
    for video in doc_video.items():
        rss_str_tl = re.sub(re.escape(str(video)), '', rss_str_tl)
        if not config.IsAir:
            img_path = dowimg(video.attr("poster"), img_proxy)
            if len(img_path) > 0:
                if config.IsLinux:
                    rss_str = re.sub(re.escape(str(video)),
                                     r'视频封面：[CQ:image,file=file:///' + re.escape(config.Linux_Path) + re.escape('data\\imgs\\') + str(
                                         img_path) + ']',
                                     rss_str)
                else:
                    rss_str = re.sub(re.escape(str(video)), r'视频封面：[CQ:image,file=file:///' + str(img_path) + ']',
                                     rss_str)
            else:
                rss_str = re.sub(re.escape(str(video)), r'视频封面：\n图片走丢啦！\n', rss_str)
        else:
            rss_str = re.sub(re.escape(str(video)), r'视频封面：' + video.attr("poster") + '\n', rss_str)



    # 翻译
    text = ''
    if translation:
        translator = Translator()
        # rss_str_tl = re.sub(r'\n', ' ', rss_str_tl)
        try:
            text=emoji.demojize(rss_str_tl)
            text = re.sub(r':[A-Za-z_]*:', ' ', text)
            text = '\n翻译：\n' + translator.translate(re.escape(text), dest='zh-CN').text
            text = re.sub(r'\\', '', text)
        except Exception as e:
            text = '\n翻译失败！'+str(e)+'\n'
    return rss_str+text


# 检查更新
def checkUpdate(new, old) -> list:
    a = new.entries
    b = old['entries']
    c = [];
    # 防止 rss 超过设置的缓存条数
    if len(a)>= config.LIMT:
        LIMT=len(a) + config.LIMT
    else:
        LIMT=config.LIMT

    for i in a:
        count = 0;
        # print(i['link'])
        for j in b:
            if i['id'] == j['id']:
                count = 1
        if count == 0:
            c.insert(0, i)
    for i in c:
        count = 0;
        # print(i['link'])
        for j in b:
            if i['id'] == j['id']:
                count = 1
        if count == 1:
            c.remove(i)
    return c


# 读取记录
def readRss(name):
    with codecs.open(file_path + name + ".json", 'r', 'utf-8') as load_f:
        load_dict = json.load(load_f)
    return load_dict


# 写入记录
def writeRss(new, name):
    # 防止 rss 超过设置的缓存条数
    if len(new.entries) >= config.LIMT:
        LIMT = len(new.entries) + config.LIMT
    else:
        LIMT = config.LIMT
    try:
        old = readRss(name)
        print(len(old['entries']))
        change = checkUpdate(new, old)

        for tmp in change:
            old['entries'].insert(0, tmp)
        count = 0;
        print(len(old['entries']))
        for i in old['entries']:
            count = count + 1
            if count > LIMT:
                old['entries'].remove(i)
    except:
        old = new

    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    with codecs.open(file_path + name + ".json", "w", 'utf-8') as dump_f:
        dump_f.write(json.dumps(old, sort_keys=True, indent=4, ensure_ascii=False))
