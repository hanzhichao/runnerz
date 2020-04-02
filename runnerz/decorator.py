from functools import wraps

from logz import log

from runnerz.keywords import NAME, CHECK, EXTRACT, CONTEXT, DATA
from runnerz.utils import do_check, do_extract, parse

functions = {}


def step(func):
    # func_name = func.__name__
    # if func_name not in functions:
    #     functions[func_name] = step(func)

    @wraps(func)
    def wapper(data, context):  # todo
        # data = parse(data, context)
        name = data.get(NAME)
        extract = data.get(EXTRACT)
        check = data.get(CHECK)

        if name:
            log.info('执行步骤', name)

        status = 'pass'
        try:
            result = func(data, context)
        except AssertionError as ex:
            log.exception(ex)
            return 'fail', None
        except Exception as ex:
            log.exception(ex)
            return 'error', None
        else:
            if extract:
                do_extract(extract, context)
            if check:
                status = do_check(check, context)
        return status, result
    return wapper

