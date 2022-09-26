import typing as t 

class Feed(t.TypedDict):
    title: str
    link: str
    subtitle: str
    updated: str


class Entrie(t.TypedDict):
    title: str
    summary: str
    published: str
    id: str
    link: str
    author: str
    guidislink: bool


class NewRss(t.TypedDict):
    bozo: bool
    encoding: str
    version: str
    headers: dict
    namespaces: dict
    feed: Feed
    entries: t.List[Entrie]


class Item(Entrie):
    hash: str
