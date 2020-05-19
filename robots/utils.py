from functools import reduce
import re

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
        log.warning('$ not in', expr)
        return expr
    if expr.startswith('$'):
        log.debug('start with $')
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