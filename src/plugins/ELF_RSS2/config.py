from pydantic import BaseSettings


class Config(BaseSettings):

    # plugin custom config
    plugin_setting: str = "default"

    class Config:
        extra = "ignore"