import re
# json中的字符串需要进行转义：
#
# ","=>&#44;、
#
# "&"=> &amp;、
#
# "["=>&#91;、
#
# "]"=>&#93;、
# 编码json，并返回CQ码
def encodeJson(json:str)->str:
    json=json.replace('\n', '').replace('\r', '')
    json=re.sub(r' ','',json)
    json=re.sub('&','&amp;',json)
    json=re.sub(',','&#44;',json)
    json=re.sub('\[','&#91;',json)
    json=re.sub(']','&#93;',json)
    return '[CQ:json,data='+json+']'

if __name__ == '__main__':
    json=encodeJson(r'''
    {
            "app":"com.tencent.miniapp",
            "desc":"",
            "view":"notification",
            "ver":"1.0.0.11",
            "prompt":"项目详情",
            "appID":"",
            "sourceName":"",
            "actionData":"",
            "actionData_A":"",
            "sourceUrl":"",
            "meta":{
                "notification":{
                    "appInfo":{
                        "appName":"QQBot made by SAGIRI",
                        "appType":4,
                        "appid":3562842879,
                        "iconUrl":"https://cdn.u1.huluxia.com/g3/M01/76/EC/wKgBOV3twseAd219AAAa0W_TXxU902.jpg"
                    },
                    "button":[
                        {
                            "action":"web",
                            "jumpurl":"https://github.com/SAGIRI-kawaii/QQBot",
                            "name":"项目地址"
                        },
                        {
                            "action":"web",
                            "url":"https://www.baidu.com",
                            "name":"博客地址"
                        },
                        {
                            "action":"",
                            "name":"文档地址（暂无）"
                        }],
                    "data":[
                        {
                            "title":"intro",
                            "value":"a Mirai-Based QQBot"
                        }
                        ],
                    "emphasis_keyword":"",
                    "title":"QQBOT 详情"
                }
            }
        }
    ''')
    print(json)
    # [CQ:json,data={"app":"com.tencent.miniapp"&#44;"desc":""&#44;"view":"notification"&#44;"ver":"0.0.0.1"&#44;"prompt":"&#91;应用&#93;"&#44;"appID":""&#44;"sourceName":""&#44;"actionData":""&#44;"actionData_A":""&#44;"sourceUrl":""&#44;"meta":{"notification":{"appInfo":{"appName":"全国疫情数据统计"&#44;"appType":4&#44;"appid":1109659848&#44;"iconUrl":"url"}&#44;"data":&#91;{"title":"确诊"&#44;"value":"80932"}&#44;{"title":"今日确诊"&#44;"value":"28"}&#44;{"title":"疑似"&#44;"value":"72"}&#44;{"title":"今日疑似"&#44;"value":"5"}&#44;{"title":"治愈"&#44;"value":"60197"}&#44;{"title":"今日治愈"&#44;"value":"1513"}&#44;{"title":"死亡"&#44;"value":"3140"}&#44;{"title":"今**亡"&#44;"value":"17"}&#93;&#44;"title":"中国加油，武汉加油"&#44;"button":&#91;{"name":"病毒：SARS-CoV-2，其导致疾病命名COVID-19"&#44;"action":""}&#44;{"name":"传染源：新冠肺炎的患者。无症状感染者也可能成为传染源。"&#44;"action":""}&#93;&#44;"emphasis_keyword":""}}&#44;"text":""&#44;"sourceAd":""}]
    # [CQ:json,data={"app":"com.tencent.miniapp"&#44;"desc":""&#44;"view":"notification"&#44;"ver":"0.0.0.1"&#44;"prompt":"&#91;应用&#93;"&#44;"appID":""&#44;"sourceName":""&#44;"actionData":""&#44;"actionData_A":""&#44;"sourceUrl":""&#44;"meta":{"notification":{"appInfo":{"appName":"全国疫情数据统计"&#44;"appType":4&#44;"appid":1109659848&#44;"iconUrl":"http:\/\/gchat.qpic.cn\/gchatpic_new\/719328335\/-2010394141-6383A777BEB79B70B31CE250142D740F\/0"}&#44;"data":&#91;{"title":"确诊"&#44;"value":"80932"}&#44;{"title":"今日确诊"&#44;"value":"28"}&#44;{"title":"疑似"&#44;"value":"72"}&#44;{"title":"今日疑似"&#44;"value":"5"}&#44;{"title":"治愈"&#44;"value":"60197"}&#44;{"title":"今日治愈"&#44;"value":"1513"}&#44;{"title":"死亡"&#44;"value":"3140"}&#44;{"title":"今**亡"&#44;"value":"17"}&#93;&#44;"title":"中国加油，武汉加油"&#44;"button":&#91;{"name":"病毒：SARS-CoV-2，其导致疾病命名 COVID-19"&#44;"action":""}&#44;{"name":"传染源：新冠肺炎的患者。无症状感染者也可能成为传染源。"&#44;"action":""}&#93;&#44;"emphasis_keyword":""}}&#44;"text":""&#44;"sourceAd":""}]