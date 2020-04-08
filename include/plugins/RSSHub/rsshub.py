# -*- coding: UTF-8 -*-
import feedparser
import json
import codecs
import re
import os.path
import requests
import uuid
import time
from datetime import datetime,timezone,timedelta
import config
import difflib

# 存储目录
file_path = './data/'
#代理
proxy = config.RSS_PROXY
proxies = {
    'http': 'http://' + proxy,
    'https': 'https://' + proxy,
}
def getRSS(url:str,name:str,img_proxy)->list:# 链接，订阅名
    # 检查是否存在rss记录
    if os.path.isfile(file_path+name+'.json'):
        d=feedparser.parse(url)#获取xml
        #print(d.feed.title)       # 通过属性访问
        change = checkUpdate(d,readRss(name))# 检查更新
        if len(change)>0 :
            writeRss(d,name)# 写入文件
            msg_list=[]
            for item in change:
                msg='【'+d.feed.title+'】更新了!\n----------------------\n'
                #处理item['summary']只有图片的情况
                text = re.sub('<video.+?><\/video>|<img.+?>', '', item['summary'])
                text = re.sub('<br>','',text)
                Similarity=difflib.SequenceMatcher(None, text, item['title'])
                #print(Similarity.quick_ratio())
                if Similarity.quick_ratio()<=0.1:# 标题正文相似度
                    msg = msg+'标题：'+item['title']+'\n'
                msg = msg+'内容：'+checkimg(item['summary'],img_proxy)+'\n'
                msg = msg+'原链接：'+item['link']+'\n'
                try:
                    loc_time=time.mktime(item['published_parsed'])
                    #print(time.localtime(loc_time))
                    msg = msg + '日期：' + time.strftime("%m月%d日 %H:%M:%S", time.localtime(loc_time))
                except BaseException:
                    msg = msg + '日期：' + time.strftime("%m月%d日 %H:%M:%S", time.localtime())
                #print(msg+'\n\n\n')
                msg_list.append(msg)
            return msg_list
        else:
            return ''
    else:
        d = feedparser.parse(url)  # 获取xml
        writeRss(d, name)  # 写入文件
        return ''

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
        return img_path + filename
    except requests.exceptions.ConnectionError:
        print('图片下载失败')
        return ''


#处理图片链接
def checkimg(img_str:str,img_proxy:bool)->str:
    pattern = re.compile(r'<img.+?>')  # 查找链接
    imgs = pattern.findall(img_str)# 带标签的图片list
    if len(imgs)>0:
        for img in imgs:
            imgg = re.search(r'\"[a-zA-z]+://[^\s]*\"', img)
            imgs_name=dowimg(imgg.group().strip('\"'),img_proxy)
            if len(imgs_name)>0:
                imgs_name=os.getcwd()+re.sub('\./', r'\\', imgs_name)
                imgs_name = re.sub(r'\\', r'\\\\', imgs_name)
                imgs_name = re.sub(r'/', r'\\\\', imgs_name)
                #print(img)
                img_str = re.sub(re.escape(img), r'[CQ:image,file=file:///'+str(imgs_name)+']', img_str)
            else:
                img_str = re.sub(re.escape(img), '\n图片走丢啦！\n', img_str)
    #下视频封面
    pattern = re.compile(r'<video.+?><\/video>')  # 查找链接
    imgs = pattern.findall(img_str)  # 带标签的图片list
    if len(imgs)>0:
        for img in imgs:
            imgg = re.search(r'poster=\"[a-zA-z]+://[^\s]*\"', img)
            imgs_name=dowimg(imgg.group().strip('poster=').strip('\"'),img_proxy)
            if len(imgs_name)>0:
                imgs_name = os.getcwd() + re.sub('\./', r'\\', imgs_name)
                imgs_name = re.sub(r'\\', r'\\\\', imgs_name)
                imgs_name = re.sub(r'/', r'\\\\', imgs_name)
                #print(imgs_name)
                img_str = re.sub(re.escape(img), str(len(imgs))+'个视频，点击原链查看[CQ:image,file=file:///'+imgs_name+']', img_str)
            else:
                img_str = re.sub(re.escape(img), '\n图片走丢啦！\n', img_str)

    #img_str = re.sub('<br><br>', '\n\n', img_str)
    img_str=re.sub('<br>','\n',img_str)
    img_str = re.sub('<p>', '', img_str)
    img_str = re.sub('</p>', '', img_str)
    pattern = re.compile(r'<a.+?>.+?</a>')  # 查找链接
    links = pattern.findall(img_str)  # a标签
    if len(links)>0:
        for a_link in links:
            a_linkk = re.search(r'[a-zA-z]+://[^\s]*</a>', a_link)
            a_linkk = a_linkk.group().strip('</a>')
            img_str = re.sub(re.escape(a_link),a_linkk+'\n',img_str)
    return img_str
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

