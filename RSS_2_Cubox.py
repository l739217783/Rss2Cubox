# encoding: utf-8
"""
@author: lin
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: 739217783@qq.com
@software: Pycharm
@file: RSS_2_cUBOX.py
@time: 2022/12/10 21:41
@desc:
"""

import json
import logging
import re
import sqlite3
import time

import requests
import schedule
from bs4 import BeautifulSoup

import cubox_api
from sqlite_operate import DBOperate


def get_story_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/74.0.3729.131 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding

    return r.text


def check_apiNum():
    """
    @return: 返回今日请求次数
    """
    today = time.strftime("%Y-%m-%d")
    num = db.dictResult(f"SELECT * FROM request_log WHERE time='{today}'")
    if num:
        return num[today]
    else:
        db.Insert(f"INSERT INTO request_log VALUES('{today}',0)")
        return 0


def get_tags(name):
    """
    根据源的名字，返回要添加的标签，用于请求Cubox时候附带标签
    @return:
    """
    tags_list = []
    data = db.Query("SELECT * FROM add_tag")

    for item in data:
        news_list = list(map(lambda x: x.strip(), item[1].split(',')))  # 通过逗号分割列表，之后移除元素中的空格
        if name in news_list:
            tags_list.append(item[0])

    if len(tags_list) > 0:
        return tags_list
    return []


def get_feed(dump_json=False):
    """
    解析OPML，获取RSS源
    dump_json:初始设置
        false:从序列化文件中读取
        true:解析OPML文件(个人是以Readyou导出格式为参考，不合适再修改)
    @return:
    """
    data = {}

    if not dump_json:
        with open(r"RSS_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        with open(r"C:\0系统库\桌面\ReadYou (1).opml", 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'xml')

        for feed in soup.find_all('outline'):
            title = feed.attrs.get('title', '')
            html_url = feed.attrs.get('htmlUrl', '')

            if html_url != '':
                # 忽略分组信息
                data[title] = html_url

        with open('RSS_data.json', 'w', encoding='utf-8') as f:
            # 序列化成json文件
            json.dump(data, f, ensure_ascii=False)
    return data


def title_check(title, desc, feed_name):
    """
    检查标题或者描述中是否存在关键字
    @param title: 标题
    @param desc:描述
    @return: bool
    """
    special_list = ['阮一峰的网络日志', '大小姐李跳跳']  # 白名单

    dont_need_title = [i[0] for i in db.Query("SELECT * FROM 标题过滤")]  # 读取已爬过链接(dict)
    for kw_title in dont_need_title:
        # 有的关键字是英文，所以采用正则忽略大小写
        if re.search(kw_title, title, re.I) or re.search(kw_title, desc, re.I):
            if feed_name not in special_list:
                # 标题或者描述存在关键字，并且不在白名单
                return True
    return False


def main():
    post_dict = {}  # 待请求队列
    exist_link = db.dictResult("SELECT * FROM ARTICLE")  # 读取已爬过链接(dict)
    api_num = check_apiNum()  # 请求次数
    sy_num = check_apiNum()  # 剩余次数，用于计算文章使用

    # 检查请求次数
    if api_num >= 200:
        logging.info('请求已达上限')
        db.CloseDB()
        return None

    # 解析环节：遍历RSS源，解析feed页面，获取页面中的链接
    for name in feeds:
        soup = BeautifulSoup(get_story_url(feeds[name]), 'xml')
        post_dict[name] = {}
        # 为每个源名，建立个子级字典用于存储标题，link;
        # {'半佛仙人': {标题1：www.baidu.com,标题2:www.bing.com}}

        for item in soup.find_all("item"):
            # 遍历文章
            title = item.title.string.replace('​', '')
            url = item.link.string
            desc = item.description.string

            if title not in exist_link:
                if title_check(title, desc, name):
                    # 如果标题或者描述中存在关键字，则跳过该文章
                    continue
                try:
                    # 标题不在已爬取记录中，则添加至数据库，加入请求队列（待请求）
                    db.Insert(f"INSERT INTO ARTICLE VALUES('{title}','{url}')")
                    post_dict[name][title] = url  # 加入请求队列
                    sy_num += 1
                except sqlite3.IntegrityError:
                    # 标题做了判断，但以防万一，写个异常处理
                    print(f"链接或标题已存在:{title}:{url}")
                    continue
            else:
                print(f'{name}：文章已爬取过，跳过：{title}')

            if sy_num >= 200:
                break
                # 如果爬取的文章数量足够，那么退出解析(退出双重for)，直接进入请求环节
        else:
            # 正常执行
            time.sleep(5)
            continue
        break

    # 请求环节：批量请求至Cubox
    for name, item in post_dict.items():
        logging.info(f'{name}：更新数量:{len(item.values())}')
        print(f'{name}：更新数量:{len(item.values())}')
        today = time.strftime("%Y-%m-%d")

        for title, link in item.items():
            print(f'{name}，抓取：{title}')
            tags = get_tags(name)
            if name == '效率火箭':
                # 效率火箭的使用自身的标题，Cubox的解析错误
                s_code = cubox_api.post_cubox(link, name, tags, title)
            else:
                s_code = cubox_api.post_cubox(link, name, tags)

            if (200 - api_num) == 0 or s_code == -3030:
                logging.info('达到上限')

                db.Update(f"UPDATE request_log SET num=200 WHERE time='{today}'")
                db.CloseDB()
                return None
            else:
                api_num += 1
                db.Update(f"UPDATE request_log SET num={api_num} WHERE time='{today}'")
                time.sleep(2)

    # 全部请求完，请求次数未达到200，运行到这，关闭数据库
    db.CloseDB()


if __name__ == '__main__':
    # 基础配置
    logging.basicConfig(filename='my.log', level=logging.DEBUG, format="%(asctime)s : %(levelname)s - %(message)s")
    db = DBOperate('RSS_config.db')
    logging.info('脚本开始运行')
    feeds = get_feed()  # 请求的feed

    schedule.every().day.at("06:00").do(main)
    schedule.every().day.at("12:00").do(main)
    while True:
        schedule.run_pending()
        time.sleep(10)
    # main()
