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
import os
import time

import requests
import schedule
from bs4 import BeautifulSoup

import cubox_api


def get_story_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"}
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding

    return r.text


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


def main():
    post_dict = {}  # 待请求队列
    notes_num = 0  # 数量统计

    if os.path.exists('3030.json'):
        print('请求已达上限')
        logging.info('请求已达上限')
        os.remove('3030.json')
        return None

    with open('exist_link.json', 'r', encoding='utf-8') as f:
        # 读取已爬取过的链接
        exist_link = json.load(f)

    # test
    # with open('a.html', 'r', encoding='utf-8') as f:
    #     html = f.read()

    # 解析环节：遍历RSS源，解析feed页面，获取页面中的链接
    for name in feeds:
        soup = BeautifulSoup(get_story_url(feeds[name]), 'xml')
        post_dict[name] = {}
        # 为每个源名，建立个子级字典用于存储标题，link;
        # {'半佛仙人': {1312：123,12313:123123}}

        for item in soup.find_all("item"):
            # 遍历文章
            title = item.title.string.replace('​', '')
            url = item.link.string

            if title not in exist_link:
                # 如果标题不在已爬取记录中，则添加
                exist_link[title] = url  # 写入爬取记录
                post_dict[name][title] = url  # 加入请求队列
                notes_num += 1
            else:
                print(f'{name}：文章已爬取过，跳过：{title}')

            if notes_num >= 200:
                break
                # 如果爬取的文章数量足够，那么退出解析(退出双重for)，直接进入请求环节
        else:
            # 正常执行
            time.sleep(5)
            continue
        break

    with open('exist_link.json', 'w', encoding='utf-8') as fw:
        # 写入已爬取过的链接
        json.dump(exist_link, fw, ensure_ascii=False)

    # 请求环节：批量请求至Cubox
    print('开始请求')
    logging.info('开始请求')

    for name, item in post_dict.items():
        logging.info(f'{name}：更新数量:{len(item.values())}')

        for title, link in item.items():
            tags = get_tags(name)
            print(f'{name}，抓取：{title}')

            s_code = cubox_api.post_cubox(link, name, tags)
            if s_code == -3030:
                print('达到上限')
                logging.info('达到上限')

                mytime = time.localtime()
                if mytime.tm_hour < 10:
                    # 如果是早上，则创建个文件，用于中午启动识别早上抓取是否达到上限
                    # 不能是下午，因为下午如果有3030这个文件，明早就无法抓取
                    with open('3030.json', 'w', encoding='utf-8') as f:
                        f.write('')
                return None
            time.sleep(2)


def get_tags(x):
    """
    根据源的名字，返回要添加的标签，用于请求Cubox时候附带标签
    @return:
    """
    tags_list = []
    data = {
        '健康': ['丁香医生', '腾讯医典'],
        '工作': ['生涯研习社', '深圳人社', '自由会客厅'],
        '软件': ['枫音应用', '效率火箭', '每日优质搜罗', '小众软件', '猿料'],
        '生活': ['国家应急广播', '老爸评测'],
        '个人成长': ['L先生说', '小猫倩倩', '曹将', '也谈钱', '阿猫读书', '罗辑思维', 'S叔Spenser'],
        '政策通报': ['深圳医保', '深圳卫健委', '深圳人社', '深圳本地宝', '广东省教育考试院'],
        '休闲': ['人物', '知乎日报', '半佛仙人'],
        '知识管理': ['flomo浮墨笔记']
    }
    for key, values in data.items():
        if x in values:
            tags_list.append(key)

    if len(tags_list) > 0:
        return tags_list
    return []


if __name__ == '__main__':
    LOG_FORMAT = "%(asctime)s : %(levelname)s - %(message)s"
    logging.basicConfig(filename='my.log', level=logging.DEBUG, format=LOG_FORMAT)

    logging.info('脚本开始运行')
    feeds = get_feed()  # 请求的feed

    schedule.every().day.at("06:00").do(main)
    schedule.every().day.at("12:00").do(main)
    while True:
        schedule.run_pending()
        time.sleep(10)
    # main()
