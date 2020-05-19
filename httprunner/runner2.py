import re
import json
import requests
import logging
from string import Template
from functools import reduce
from operator import eq, gt, lt, ge, le
import unittest


def parse_config(config):
    pass


def do_dot(item, key):
    print(item, key)
    if hasattr(item, key):
        return getattr(item, key)
    if key.isdigit():
        key = int(key)
    try:
        return item[key]
    except Exception as ex:
        logging.exception(ex)
        return key

def get_field(context, expr):
    if '.' in expr:
        value = expr.split('.')
        print(value[0])
        field = context.get(value[0])
        print('field', field)
        return reduce(lambda x, y: do_dot(x, y), value[1:], field)
    else:
        return context.get(expr)

class TestApi(unittest.TestCase):
    """{{suite_name}}"""
    def setUpClass(cls):
        pass








# 1. 实现步骤解析
def run(data):
    config = data[0].get('config')
    suite_name = config.get('name')
    variables = config.get('variables', {})
    config_request = config.get('request')
    base_url = config_request.pop('base_url') if 'base_url' in config_request else None
    print('base_url', base_url)

    # 设置上下文变量
    context = variables

    # 设置请求默认值
    session = requests.session()
    for key, value in config_request.items():
        setattr(session, key, value)

    # 添加setUpClass
    def setUpClass(cls):
        # 设置上下文变量
        cls.context = variables

        # 设置请求默认值
        session = requests.session()
        for key, value in config_request.items():
            setattr(session, key, value)

    # 解析步骤
    for item in data[1:]:
        test = item.get('test')
        name = test.get('name')
        request = test.get('request')
        extract = test.get('extract', [])
        validate = test.get('validate', [])

        # 组装base_url
        if base_url and not request['url'].startswith('http'):
            request['url'] = base_url + request['url']

        # 发请求
        response = session.request(**request)
        try:
            content = response.json()
        except json.decoder.JSONDecodeError:
            content = {}

        # 注册上下文变量
        context.update(
            response=response,
            request=response.request,
            content=content,
            status_code=response.status_code,
            headers=response.headers,
            ok=response.ok,
            reason=response.reason,
            response_time=response.elapsed.seconds
        )

        # 处理提取变量
        for line in extract:

            key, value = tuple(line.items())[0]
            context[key] = get_field(context, value)


        # 处理断言
        compare_funcs = dict(eq=eq, gt=gt, lt=lt, ge=ge, le=le,
                             len_eq=lambda x, y: len(x) == len(y),

                             str_eq=lambda x, y: str(x) == str(y),
                             type_match=lambda x, y: isinstance(x, y),
                             regex_match=lambda x, y: re.match(y, x)

                             )
        for line in validate:
            if 'comparator' in line:
                comparator = line.get('comparator')
                check = line.get('check')
                expect = line.get('expect')
            else:
                comparator, value = tuple(line.items())[0]
                check, expect = value
            compare_func = compare_funcs.get(comparator)
            field = get_field(context, check)
            assert compare_func(field, expect)






if __name__ == '__main__':
    from filez import file
    data = file.load('/Users/apple/Documents/Projects/Self/PyPi/runnerz/httprunner/data.yaml')
    print(data)
    run(data)
