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
# 存储目录
file_path = './data/'
#代理
proxy = config.RSS_PROXY
proxies = {
    'http': 'http://' + proxy,
    'https': 'https://' + proxy,
}
def getRSS(rss:RSS_class.rss)->list:# 链接，订阅名
    # 检查是否存在rss记录
    if os.path.isfile(file_path+rss.name+'.json'):
        d=feedparser.parse(rss.geturl())#获取xml
        #print(d.feed.title)       # 通过属性访问
        change = checkUpdate(d,readRss(rss.name))# 检查更新
        if len(change)>0 :
            writeRss(d,rss.name)# 写入文件
            msg_list=[]
            for item in change:
                msg='【'+d.feed.title+'】更新了!\n----------------------\n'

                if not rss.only_title :
                    # 处理item['summary']只有图片的情况
                    text = re.sub('<video.+?><\/video>|<img.+?>', '', item['summary'])
                    text = re.sub('<br>', '', text)
                    Similarity = difflib.SequenceMatcher(None, text, item['title'])
                    # print(Similarity.quick_ratio())
                    if Similarity.quick_ratio() <= 0.1:  # 标题正文相似度
                        msg = msg + '标题：' + item['title'] + '\n'
                    msg = msg + '内容：' + checkstr(item['summary'], rss.img_proxy,rss.translation) + '\n'
                else:
                    msg = msg + '标题：' + item['title'] + '\n'

                msg = msg+'原链接：'+item['link']+'\n'

                try:
                    loc_time = time.mktime(item['published_parsed'])
                    msg = msg + '日期：' + time.strftime("%m月%d日 %H:%M:%S", time.localtime(loc_time + 28800.0))
                except BaseException:
                    msg = msg + '日期：' + time.strftime("%m月%d日 %H:%M:%S", time.localtime())
                #print(msg+'\n\n\n')
                msg_list.append(msg)
            return msg_list
        else:
            return []
    else:
        d = feedparser.parse(rss.geturl())  # 获取xml
        try:
            d.feed.title
            writeRss(d, rss.name)  # 写入文件
        except:
            logger.info('获取 '+rss.name+' 订阅xml失败！！！请检查订阅地址是否可用！')
        return []

# 下载图片
def dowimg(url:str,img_proxy:bool)->str:
    img_path = file_path+'imgs'+ os.sep
    if not os.path.isdir(img_path):
        print(img_path+'文件夹不存在，已重新创建')
        os.makedirs(img_path)  # 创建目录

    file_suffix = os.path.splitext(url)  # 返回列表[路径/文件名，文件后缀]
    name = str(uuid.uuid4())
    try:
        if img_proxy :
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
        imgs_name=img_path + filename
        if len(imgs_name) > 0:
            imgs_name = os.getcwd() + re.sub('\./', r'\\', imgs_name)
            imgs_name = re.sub(r'\\', r'\\\\', imgs_name)
            imgs_name = re.sub(r'/', r'\\\\', imgs_name)
        return imgs_name
    except requests.exceptions.ConnectionError:
        print('图片下载失败')
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
        img_path = dowimg(img.attr("src"), img_proxy)
        if len(img_path) > 0:
            rss_str = re.sub(re.escape(str(img)), r'[CQ:image,file=file:///' + str(img_path) + ']', rss_str)
        else:
            rss_str = re.sub(re.escape(str(img)), r'\n图片走丢啦！\n', rss_str, re.S)
        rss_str_tl = re.sub(re.escape(str(img)), '', rss_str_tl)
        # 处理视频
    doc_video = doc_rss('video')
    for video in doc_video.items():
        img_path = dowimg(video.attr("poster"), img_proxy)
        if len(img_path) > 0:
            rss_str = re.sub(re.escape(str(video)), '视频封面：[CQ:image,file=file:///' + str(img_path) + ']', rss_str)
        else:
            rss_str = re.sub(re.escape(str(video)), r'视频封面：\n图片走丢啦！\n', rss_str)
        rss_str_tl = re.sub(re.escape(str(video)), '', rss_str_tl)
    # 翻译
    text = ''
    if translation:
        translator = Translator()
        # rss_str_tl = re.sub(r'\n', ' ', rss_str_tl)
        try:
            text = '\n翻译：\n' + translator.translate(re.escape(rss_str_tl), dest='zh-CN').text
            text = re.sub(r'\\', '', text)
        except:
            text = '\n翻译失败！请联系管理员！\n'
    return rss_str+text


# 检查更新
def checkUpdate(new,old)->list:
    a=new.entries
    b=old['entries']
    c=[];

    for i in a:
        count = 0;
        for j in b:
            if i['link'] == j['link']:
                count=1
        if count==0 :
            c.append(i)
    return c
# 读取记录
def readRss(name):
    with codecs.open(file_path+name+".json", 'r','utf-8') as load_f:
        load_dict = json.load(load_f)
    return load_dict
# 写入记录
def writeRss(d,name):
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    with codecs.open(file_path+name+".json", "w",'utf-8') as dump_f:
        dump_f.write(json.dumps(d, sort_keys=True, indent=4, ensure_ascii=False))

