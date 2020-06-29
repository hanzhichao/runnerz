import os
import sys
import yaml
from string import Template
import operator
import importlib

from logz import log

from runnerz.keywords import ACTION, SUB_STEPS, FUNCTIONS, VAIABLES

BASEDIR = os.path.dirname(os.path.dirname(__file__))

FIXTURES_FILE = 'fixtures'



def get_section(data, keywords):
    if not isinstance(keywords, (str, list)):
        raise TypeError('keywords must be str or list')

    if isinstance(keywords, str):
        return data.get(keywords)
    if isinstance(keywords, list):
        for keyword in keywords:
            section = data.get(keyword)
            if section is not None:
                return section


def is_step(data):
    return True if get_section(data, SUB_STEPS) is None else False


def get_function(data, context=None):
    if context is None:
        return
    functions = context.get(FUNCTIONS)
    action = data.get(ACTION)
    if action:
        return functions.get(action)

    for action in functions.keys() - {'name', 'key', 'skip', 'extract', 'validate'}:
        function = functions.get(action)
        if function is not None:
            return function


def parse(data, context):
    variables = context.get(VAIABLES)
    if variables is None:
        return data

    data_str = yaml.safe_dump(data, default_flow_style=False)
    if '$' in data_str:
        data_str = Template(data_str).safe_substitute(variables)
        data = yaml.safe_load(data_str)
    return data


def do_extract(data: (dict, list), context):
    if isinstance(data, dict):   # dict -> list
        data = [data]
    variables = context.get(VAIABLES)
    for line in data:
        if not isinstance(line, dict):
            raise TypeError(f'line: {line} 必须为字典格式')
        for key, value in line.items():
            print("提取变量:", key, value)
            variables[key] = eval(value, {}, variables)  # 保存变量结果到局部变量中


def do_check(data, context):
    variables = context.get(VAIABLES)
    for line in data:
        if isinstance(line, str):
            result = eval(line, {}, variables)  # 计算断言表达式，True代表成功，False代表失败
        elif isinstance(line, dict):
            for key, value in line.items():
                if hasattr(operator, key):
                    func = getattr(operator, key)
                    for index, item in enumerate(value):
                        if isinstance(item, str):
                            value[index] = variables.get(item) or item
                    result = func(*value)
        print("处理断言:", line, "结果:", "PASS" if result else "FAIL")


def merge_update(dict1, dict2):
    """融合子属性中的字典和列表类型"""
    for item, value in dict2.items():
        if item in dict1:
            if isinstance(value, dict) and isinstance(dict1[item], dict):
                merge_update(dict1[item], dict2[item])
                continue
            if isinstance(item, list) and isinstance(dict1[item], list):
                dict1[item].extend(dict2[item])
                continue
        dict1[item] = dict2[item]


def get_model_functions(model):
    functions = {attr: func for attr, func in model.__dict__.items()
                 if not attr.startswith('__')}
    return functions


def get_fixtures():
    try:
        fixtures = importlib.import_module(FIXTURES_FILE)
    except Exception as ex:
        log.exception(ex)
        return {}
    return get_model_functions(fixtures)