import time


# 处理日期
async def handle_date(date=None) -> str:
    if date:
        if not isinstance(date, tuple):
            date = tuple(date)
        rss_time = time.mktime(date)
        # 时差处理，待改进
        if rss_time + 28800.0 < time.time():
            rss_time += 28800.0
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime(rss_time))
    # 没有日期的情况，以当前时间
    else:
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime())
