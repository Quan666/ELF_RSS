#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ELF_RSS",
    version="2.4.4",
    author="Quan666",
    author_email="i@oy.mk",
    description="QQ机器人 RSS订阅 插件，订阅源建议选择 RSSHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Quan666/ELF_RSS",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
