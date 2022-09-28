import typing as t


class Feed(t.TypedDict):
    title: str
    link: str
    subtitle: str
    updated: str


class Entry(t.TypedDict):
    title: str
    summary: str
    published: str
    id: str
    link: str
    author: str
    guid_is_link: bool


class NewRss(t.TypedDict):
    bozo: bool
    encoding: str
    version: str
    headers: t.Dict[t.Any, t.Any]
    namespaces: t.Dict[t.Any, t.Any]
    feed: Feed
    entries: t.List[Entry]


class Item(Entry):
    hash: str
