import unittest
import types
import re
from functools import reduce
from string import Template

import requests

from logz import log, logit
from filez import file
from robots.utils import split_and_strip, parse_dollar, get_comparator
print = log.info



def extract(expr):
    return expr


functions = dict(
    log=log.info,
    get=requests.get,
    extract=extract
)


def parse_args(context: dict, *args):
    return [parse_dollar(context, arg) for arg in args]


def parse_kwargs(context: dict, **kwargs):
    return {parse_dollar(context, key): parse_dollar(context, value) for key, value in kwargs.items()}


def do_filter2(result, text):
    comparator = get_comparator(text)
    if comparator:
        text = split_and_strip(text, comparator)

    context = dict(result=result)
    value = parse_dollar(context, text)
    # filter_result = eval(str(text), {}, context)
    # if is_expr(text):
    #     assert eval(text, {}, dict(result=result))
    #     return result
    return text


def do_function(context, expr):
    if isinstance(expr, str):
        func_name, *args = expr.split()
        key = None
        if '=' in func_name:
            key, func_name = split_and_strip(func_name, '=')

        kwargs = {item.split('=', 1)[0]: item.split('=', 1)[1] for item in args if '=' in item}
        args = [item for item in args if '=' not in item]
        args = parse_args(context, *args)
        kwargs = parse_kwargs(context, **kwargs)
        func = functions.get(func_name)
        print('func', func)
        if func:
            result = func(*args, **kwargs)
            if key:
                context[key] = result
            return result


def do_filter(context, expr):
    # context = dict(result=result)
    result = do_function(context, expr)
    # do_step(context)
    return result


def do_step(context, expr: (str, dict)):
    filters = None
    # if isinstance(expr, dict):
    #     key, expr = tuple(expr.items())[0]  # fixme
    global functions  # fixme
    if '|' in expr:
        expr, *filters = split_and_strip(expr, '|')


    result = do_function(context, expr)
    context['result'] = result
    if filters:
        for expr in filters:
            log.debug('do filter', expr)
            result = do_filter(context, expr)


def build_keyword(name: str, attrs: dict) -> dict:
    doc = attrs.get('Documention')
    arg_names = attrs.get('Arguments', [])
    steps = attrs.get('Steps', [])
    func_return = attrs.get('Return')
    # context = locals()

    def func(*args):
        kwargs = dict(zip(arg_names, args))
        locals().update(kwargs)
        for step in steps:
            do_step(locals(), step)
        return locals().get('func_return')

    func.__name__ = name
    func.__doc__ = doc
    return {name: func}


def handle_keywords(keywords: dict) -> None:
    global functions  # fixme
    [functions.update(build_keyword(name, attrs)) for name, attrs in keywords.items()]


def build_case(index:int, test: dict) -> types.FunctionType:
    name, attrs = tuple(test.items())[0]
    def test_method(self):
        if attrs.get('Skip'):
            raise unittest.SkipTest('Skip=True跳过用例')
        if attrs.get('Variables'):
            self.context.update(attrs.get('Variables'))
        steps = attrs.get('Steps')
        for step in steps:
            do_step(self.context, step)

    test_method.__name__ = f'test_{index+1}'
    test_method.__doc__ = attrs.get('Documentation')
    test_method.name = name
    test_method.tags = attrs.get('Tags')
    test_method.timeout = attrs.get('Timeout')
    return test_method


def build(data: dict):
    context = variables = data.get('Variables')

    class TestRobot(unittest.TestCase):
        @classmethod
        def setUpClass(cls) -> None:
            cls.context = context

    keywords = data.get('Keywords')
    handle_keywords(keywords)

    tests = data.get('TestCases')
    [setattr(TestRobot, f'test_{index+1}', build_case(index, test)) for index, test in enumerate(tests)]

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRobot)
    return suite


def run(suite):
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


# def test_is_expr():
#     assert is_expr('status_code == 200')
#     assert is_expr('status_code is True')
#     assert not is_expr('content.url')

if __name__ == '__main__':
    text = 'log hello,world'
    # do_step(text)
    data = file.load('/Users/apple/Documents/Projects/Self/PyPi/runnerz/robots/data.yaml')
    suite = build(data)
    run(suite)
