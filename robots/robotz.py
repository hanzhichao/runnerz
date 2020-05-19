import unittest
import types
import re
from functools import reduce
from string import Template

import requests

from logz import log, logit
from filez import file

print = log.info









@logit()
def extract(result, expr):
    return get_field(dict(result=result), expr)


functions = dict(
    log=log.info,
    get=requests.get,
    extract=extract
)





def parse_args(context: dict, *args):
    return [parse_dollar(context, arg) for arg in args]


def parse_kwargs(context: dict, **kwargs):
    return {parse_dollar(context, key): parse_dollar(context, value) for key, value in kwargs.items()}


def get_comparator(text):
    for comparator in ['==', 'is not', 'is', 'not in', 'in', 'not', '>', '<', '>=', '<=']:
        if comparator in text:
            return comparator


def do_filter2(result, text):
    comparator = get_comparator(text)
    if comparator:
        text = split_and_strip(text, comparator)

    context = dict(result=result)
    log.debug('do_filter', result, text)
    value = parse_dollar(context, text)
    log.debug('pared text', text)
    # filter_result = eval(str(text), {}, context)
    # if is_expr(text):
    #     assert eval(text, {}, dict(result=result))
    #     return result
    return text


def do_function(context, expr):
    log.debug('do function', expr)
    if isinstance(expr, str):
        func_name, *args = expr.split()
        print('args', args)
        key = None
        if '=' in func_name:
            key, func_name = split_and_strip(func_name, '=')

        kwargs = {item.split('=', 1)[0]: item.split('=', 1)[1] for item in args if '=' in item}
        args = [item for item in args if '=' not in item]
        args = parse_args(context, *args)
        kwargs = parse_kwargs(context, **kwargs)
        func = functions.get(func_name)
        if func:
            log.debug('do func', func.__name__, args, kwargs)
            result = func(*args, **kwargs)
            context['result'] = context['$'] = result

            if key:
                context[key] = result
                log.warning(context)
            return result


def do_filter(context, expr):
    print('do filter', expr)
    # context = dict(result=result)
    print(context, expr)
    result = do_function(context, expr)
    # do_step(context)
    print('do filter result', result, context)
    return result


def do_step(context, expr: (str, dict)):
    log.debug('do step', expr)
    filters = None
    # if isinstance(expr, dict):
    #     key, expr = tuple(expr.items())[0]  # fixme
    global functions  # fixme
    if '|' in expr:
        expr, *filters = split_and_strip(expr, '|')

        print('expr', expr, 'filters', filters)

    result = do_function(context, expr)
    if filters:
        for expr in filters:
            do_filter(context, expr)







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
