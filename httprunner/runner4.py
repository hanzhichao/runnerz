import re
import json
import requests
import logging
from string import Template
from functools import reduce
from operator import eq, gt, lt, ge, le
import unittest
import ddt
import importlib
import jinja2


COMPARE_FUNCS = dict(
    eq=eq, gt=gt, lt=lt, ge=ge, le=le,
    len_eq=lambda x, y: len(x) == len(y),

    str_eq=lambda x, y: str(x) == str(y),
    type_match=lambda x, y: isinstance(x, y),
    regex_match=lambda x, y: re.match(y, x)
)


def do_dot(item, key):
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
        field = context.get(value[0])
        return reduce(lambda x, y: do_dot(x, y), value[1:], field)
    else:
        return context.get(expr)


def send_request(context, base_url, session, request):
    # 组装base_url
    if base_url and not request['url'].startswith('http'):
        request['url'] = base_url + request['url']

    # 发请求
    response = session.request(**request)
    print('响应数据', response.text)
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


def do_extract(context, extract):
    # 处理提取变量
    for line in extract:
        key, value = tuple(line.items())[0]
        context[key] = get_field(context, value)


def do_validate(context, validate):
    # 处理断言
    for line in validate:
        if 'comparator' in line:
            comparator = line.get('comparator')
            check = line.get('check')
            expect = line.get('expect')
        else:
            comparator, value = tuple(line.items())[0]
            check, expect = value
        compare_func = COMPARE_FUNCS.get(comparator)
        field = get_field(context, check)
        assert compare_func(field, expect)


def get_functions():
    """从模块中获取功能函数"""
    module = importlib.import_module('debugtalk')
    functions = {key: value for key, value in module.__dict__.items()
                 if not key.startswith('__') and callable(value)}
    return functions


def parse_dollar(context, data):
    """解析$变量"""
    data_str = json.dumps(data)
    if '$' in data_str:
        data_str = Template(data_str).safe_substitute(context)
        return json.loads(data_str)
    else:
        return data

# 1. 实现步骤解析
def build(data):
    config = data[0].get('config')
    functions = get_functions()

    @ddt.ddt
    class TestApi(unittest.TestCase):
        f"""{config.get('name')}"""
        @classmethod
        def setUpClass(cls):
            cls.session = requests.session()
            config_request = config.get('request')
            cls.base_url = config_request.pop('base_url') if 'base_url' in config_request else None
            cls.context = config.get('variables', {})
            for key, value in config_request.items():
                setattr(cls.session, key, value)

        @ddt.data(*data[1:])
        def test_api(self, test):
            f"""{test.get('name')}"""
            test = test.get('test')
            if test.get('skip'):
                raise unittest.SkipTest
            parameters = test.get('parameters')
            if parameters:
                for line in parameters:
                    keys, data = tuple(line.items())[0]
                    keys = keys.split('-')
                    for item in data:
                        for index, key in enumerate(keys):
                            self.context[key] = item[index]
                        with self.subTest():
                            parsed_test = parse_dollar(self.context, test)
                            send_request(self.context, self.base_url, self.session, parsed_test.get('request'))
                            do_extract(self.context, parsed_test.get('extract', []))
                            do_validate(self.context, parsed_test.get('validate', []))
            else:
                parsed_test = parse_dollar(self.context, test)
                send_request(self.context, self.base_url, self.session, parsed_test.get('request'))
                do_extract(self.context, parsed_test.get('extract', []))
                do_validate(self.context, parsed_test.get('validate', []))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestApi)
    return suite


def run(suite):
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)



if __name__ == '__main__':
    from filez import file
    data = file.load('/Users/apple/Documents/Projects/Self/PyPi/runnerz/httprunner/data.yaml')
    suite = build(data)
    run(suite)
    # build_case(data)