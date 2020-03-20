import requests


def http_get(url, **kwargs):
    if 'context' in kwargs:
        kwargs.pop('context')
    return requests.get(url, **kwargs)


def http_post(url, **kwargs):
    if 'context' in kwargs:
        kwargs.pop('context')
    return requests.post(url, **kwargs)


# print(data)
def extract_expr(expr, context):
    if not isinstance(expr, str):
        raise TypeError('expr应为str格式')

    if expr.startswith('$.') and 'response' in context:
        root = context['response'].json()
        value = jsonpath(context[root], expr)
        return value


def extract(extract_dict, context):
    if not isinstance(extract_dict, dict):
        raise TypeError('extract_dict应为dict格式')

    for key, expr in extract_dict.items():
        context[key] = extract_expr(expr, context)


def check_expr(expr, context):
    if not isinstance(expr, str):
        raise TypeError('expr应为str格式')
    indent = ' ' * 6
    print(f'{indent}执行断言: {expr}')
    try:
        assert eval(expr, {}, context)
    except Exception as ex:
        print('断言失败', ex)
        return False
    else:
        return True


def check(check_list, context):
    if not isinstance(check_list, list):
        raise TypeError(f'check_list: {check_list}应为list类型')

    for expr in check_list:
        check_expr(expr, context)


def request(**kwargs):
    if 'check' in kwargs:
        _check = kwargs.pop('check')
    if 'extract' in kwargs:
        _extract = kwargs.pop('extract')
    context = kwargs.pop('context')
    res = requests.request(**kwargs)
    return res