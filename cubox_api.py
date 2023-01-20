# encoding: utf-8
"""
@author: lin
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: 739217783@qq.com
@software: Pycharm
@file: cubox_api.py
@time: 2022/6/5 15:33
@desc:Cubox API
"""
import requests
import json


def post_cubox(cubox_content, folder, tags=[], title=None):
    """
    cubox_content：url地址
    folder:放的位置
    tags:需要添加的标签
    """
    url = 'https://cubox.pro/c/api/save/7ggtqtt0qml77j'
    data = {
        # "type": "Demo",
        # "content": "Demo",
        "type": "url",
        "content": f"{cubox_content}",
        "tags": tags,
        "folder": folder
    }
    if title:
        # 有传标题的话，使用传入的标题，否则让Cubox自己解析生成
        data['title'] = title

    headers = {
        "Content-Type": "application/json", "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/74.0.3729.131 Safari/537.36"
    }

    result = requests.post(url, headers=headers, data=json.dumps(data))
    status_code = json.loads(result.text)['code']

    # if status_code == 200:
    #     print('上传成功')
    # else:
    #     print(result.text)

    return status_code


if __name__ == '__main__':
    pass
