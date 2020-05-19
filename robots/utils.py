from functools import reduce
import re
import json

from logz import log, logit

VAR_PARTTERN = re.compile('\$(\w+.?\w+|\w)')


def split_and_strip(text, seq):
    return [item.strip() for item in text.split(seq)]


@logit()
def do_dot(item, key: str):
    """单个content.url取值"""
    value = None
    if hasattr(item, key):
        value = getattr(item, key)
    else:
        if key.isdigit():
            key = int(key)
        try:
            value = item[key]
        except Exception as ex:
            log.exception(ex)
    return value() if callable(value) else value


@logit()
def get_field(context: dict, expr: str):
    """解析形如content.result.0.id的取值"""
    assert isinstance(context, dict)
    if '.' in expr:
        value = expr.split('.')
        field = context.get(value[0])
        field = reduce(lambda x, y: do_dot(x, y), value[1:], field)
        return field() if callable(field) else field
    else:
        return context.get(expr, expr)


@logit()
def parse_dollar(context: dict, expr: str):
    """解析$变量"""
    if '$' not in expr:
        return expr
    if expr.startswith('$'):
        return get_field(context, expr.strip('$'))

    def repr_func(matched):
        """自定义re.sub替换方法"""
        if not matched:
            return
        origin = matched.group(1)
        return str(get_field(context, origin))
    return re.sub(VAR_PARTTERN, repr_func, expr)

@logit()
def get_comparator(text):
    for comparator in ['==', 'is not', 'is', 'not in', 'in', 'not', '>', '<', '>=', '<=']:
        if comparator in text:
            return comparator


# def parse_list(context: dict, data: list) -> list:
#     return [parse_dollar(context, arg) for arg in data]
#
#
# def parse_dict(context: dict, data: dict) -> dict:
#     return {parse_dollar(context, key): parse_dollar(context, value) for key, value in data.items()}


# import re
# import json


def parser(origin,*args, delimiter="$", **kwargs):  # 支持修改delimiter定界符

    patten = r'\{}(?P<var>.+?)'.format(delimiter)

    def repl_func(matched):   # 自定义re.sub使用的替换方法
        var = matched.group('var')
        if var.isdigit():   # 如果是数字, 则从args中替换
            index = int(var) - 1
            if index < len(args):
                return args[index]
            else:
                return "{}{}".format(delimiter, var)   # 无替换参数则返回原值
        else:
            return kwargs.get(var, None) or "{}{}".format(delimiter, var)   # 返回kwargs参数中值 or 原值

    if isinstance(origin, str):
        return re.sub(patten, repl_func, origin, re.M)
    elif isinstance(origin, (dict, list)):  # 使用json.dumps转为字符串, 替换,然后重新转为dict/list
        return json.loads(re.sub(patten, repl_func, json.dumps(origin), re.M))
    else:
        if isinstance(origin, tuple):
            return tuple(json.loads(re.sub(patten, repl_func, json.dumps(origin), re.M)))  # 转换后重新转为tuple


if __name__ == '__main__':
    s = ['性别: $2  年龄: $3\n$a', '$1', {"say": "$a"}]
    print(parser(s, 'kevin', 'male', '20', a="hello, world!"))