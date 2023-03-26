import re
from html import unescape as html_unescape

import bbcode
from pyquery import PyQuery as Pq
from yarl import URL

from ..config import config


# 处理 bbcode
def handle_bbcode(html: Pq) -> str:
    rss_str = html_unescape(str(html))

    # issue 36 处理 bbcode
    rss_str = re.sub(
        r"(\[url=[^]]+])?\[img[^]]*].+\[/img](\[/url])?", "", rss_str, flags=re.I
    )

    # 处理一些 bbcode 标签
    bbcode_tags = [
        "align",
        "b",
        "backcolor",
        "color",
        "font",
        "size",
        "table",
        "tbody",
        "td",
        "tr",
        "u",
        "url",
    ]

    for i in bbcode_tags:
        rss_str = re.sub(rf"\[{i}=[^]]+]", "", rss_str, flags=re.I)
        rss_str = re.sub(rf"\[/?{i}]", "", rss_str, flags=re.I)

    # 去掉结尾被截断的信息
    rss_str = re.sub(
        r"(\[[^]]+|\[img][^\[\]]+) \.\.\n?</p>", "</p>", rss_str, flags=re.I
    )

    # 检查正文是否为 bbcode ，没有成对的标签也当作不是，从而不进行处理
    bbcode_search = re.search(r"\[/(\w+)]", rss_str)
    if bbcode_search and re.search(f"\\[{bbcode_search[1]}", rss_str):
        parser = bbcode.Parser()
        parser.escape_html = False
        rss_str = parser.format(rss_str)

    return rss_str


def handle_lists(html: Pq, rss_str: str) -> str:
    # 有序/无序列表 标签处理
    for ul in html("ul").items():
        for li in ul("li").items():
            li_str_search = re.search("<li>(.+)</li>", repr(str(li)))
            rss_str = rss_str.replace(
                str(li), f"\n- {li_str_search[1]}"  # type: ignore
            ).replace("\\n", "\n")
    for ol in html("ol").items():
        for index, li in enumerate(ol("li").items()):
            li_str_search = re.search("<li>(.+)</li>", repr(str(li)))
            rss_str = rss_str.replace(
                str(li), f"\n{index + 1}. {li_str_search[1]}"  # type: ignore
            ).replace("\\n", "\n")
    rss_str = re.sub("</(ul|ol)>", "\n", rss_str)
    # 处理没有被 ul / ol 标签包围的 li 标签
    rss_str = rss_str.replace("<li>", "- ").replace("</li>", "")
    return rss_str


# <a> 标签处理
def handle_links(html: Pq, rss_str: str) -> str:
    for a in html("a").items():
        a_str = re.search(
            r"<a [^>]+>.*?</a>", html_unescape(str(a)), flags=re.DOTALL
        ).group()  # type: ignore
        if a.text() and str(a.text()) != a.attr("href"):
            # 去除微博超话
            if re.search(
                r"https://m\.weibo\.cn/p/index\?extparam=\S+&containerid=\w+",
                a.attr("href"),
            ):
                rss_str = rss_str.replace(a_str, "")
            # 去除微博话题对应链接 及 微博用户主页链接，只保留文本
            elif (
                a.attr("href").startswith("https://m.weibo.cn/search?containerid=")
                and re.search("#.+#", a.text())
            ) or (
                a.attr("href").startswith("https://weibo.com/")
                and a.text().startswith("@")
            ):
                rss_str = rss_str.replace(a_str, a.text())
            else:
                if a.attr("href").startswith("https://weibo.cn/sinaurl?u="):
                    a.attr("href", URL(a.attr("href")).query["u"])
                rss_str = rss_str.replace(a_str, f" {a.text()}: {a.attr('href')}\n")
        else:
            rss_str = rss_str.replace(a_str, f" {a.attr('href')}\n")
    return rss_str


# HTML标签等处理
def handle_html_tag(html: Pq) -> str:
    rss_str = html_unescape(str(html))

    rss_str = handle_lists(html, rss_str)
    rss_str = handle_links(html, rss_str)

    # 处理一些 HTML 标签
    html_tags = [
        "b",
        "blockquote",
        "code",
        "dd",
        "del",
        "div",
        "dl",
        "dt",
        "em",
        "figure",
        "font",
        "i",
        "iframe",
        "ol",
        "p",
        "pre",
        "s",
        "small",
        "span",
        "strong",
        "sub",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "u",
        "ul",
    ]

    # <p> <pre> 标签后增加俩个换行
    for i in ["p", "pre"]:
        rss_str = re.sub(f"</{i}>", f"</{i}>\n\n", rss_str)

    # 直接去掉标签，留下内部文本信息
    for i in html_tags:
        rss_str = re.sub(f"<{i} [^>]+>", "", rss_str)
        rss_str = re.sub(f"</?{i}>", "", rss_str)

    rss_str = re.sub(r"<(br|hr)\s?/?>|<(br|hr) [^>]+>", "\n", rss_str)
    rss_str = re.sub(r"<h\d [^>]+>", "\n", rss_str)
    rss_str = re.sub(r"</?h\d>", "\n", rss_str)

    # 删除图片、视频标签
    rss_str = re.sub(
        r"<video[^>]*>(.*?</video>)?|<img[^>]+>", "", rss_str, flags=re.DOTALL
    )

    # 去掉多余换行
    while "\n\n\n" in rss_str:
        rss_str = rss_str.replace("\n\n\n", "\n\n")
    rss_str = rss_str.strip()

    if 0 < config.max_length < len(rss_str):
        rss_str = f"{rss_str[: config.max_length]}..."

    return rss_str
