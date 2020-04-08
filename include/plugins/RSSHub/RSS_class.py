import config
class rss:
    # 定义基本属性
    name = '' # 订阅名
    url = '' # 订阅地址
    user_id=[] # 订阅用户（qq） -1 为空
    group_id=[] # 订阅群组
    notrsshub=False # 是否非rsshub订阅
    img_proxy=False
    sum=20 # 加载条数
    time=5 #更新频率 分钟/次
    # 定义构造方法
    def __init__(self,name:str, url:str, user_id:str, group_id:str,time=5,img_proxy=False,notrsshub=False):
        self.name = name
        self.url = url
        if user_id!='-1' :
            self.user_id = user_id.split(',')
        if group_id!='-1' :
            self.group_id = group_id.split(',')
        self.notrsshub=notrsshub
        self.time=time
        self.img_proxy=img_proxy

    def geturl(self)->str:
        if self.notrsshub :
            return self.url
        else:
            return config.RSSHUB+self.url
