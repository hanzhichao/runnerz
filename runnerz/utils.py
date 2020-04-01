import yaml
from string import Template
import operator

from runnerz.keywords import ACTION, SUB_STEPS, FUNCTIONS, VAIABLES

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
    return False if get_section(data, SUB_STEPS) else True


def get_function(data, context=None):
    if context is None:
        return
    functions = context.get(FUNCTIONS)
    action = data.get(ACTION)
    if action:
        return functions.get(action)

    for action in functions.keys():
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


def do_extract(data, context):
    variables = context.get(VAIABLES)
    for key, value in data.items():
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
                    value = [variables.get(item) or item for item in value]
                    result = func(*value)
        print("处理断言:", line, "结果:", "PASS" if result else "FAIL")