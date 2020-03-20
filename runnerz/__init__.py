import yaml
import os
from collections import ChainMap, namedtuple

from string import Template
from jsonpath import jsonpath
from actions import request
# import chrome



def parse_func_args(func_args, context):
    indent = ' ' * 6
    print(f'{indent}解析参数: {func_args}')
    if not func_args:
        return func_args

    if isinstance(func_args, str):
        func_args_string = func_args
    elif isinstance(func_args, (list, tuple, dict)):
        func_args_string = yaml.dump(func_args, default_flow_style=False)

    if '$' not in func_args_string:
        return func_args

    values = ChainMap(context.get('args', {}), context.get('variables', {}), context.get('defaults', {}))
    # print(f'{indent}values值: {values}')
    # print('func_args_string', func_args_string)
    func_args_string = Template(func_args_string).safe_substitute(values)
    # print('func_args_string', func_args_string)
    func_args = yaml.safe_load(func_args_string)
    print(f'{indent}解析后的参数: {func_args}')
    return func_args


def do_func(func, func_args, context):
    if not func:
        return
    result = context.get('result', [])
    stage_index = context.get('stage_index', 0)
    step_index = context.get('step_index', 0)
    func_hook = context.get('func_hook', print)
    indent = ' ' * 6
    try:
        print(f'{indent}调用函数: {func.__name__} 参数: {func_args}')
        if isinstance(func_args, dict):
            func_args['context'] = context
            func_result = func(**func_args)
        elif isinstance(func_args, (list, tuple)):
            # func_args.append(context)
            func_result = func(func_args, context)
            # func_result = func(*func_args)
        else:
            func_result = func(func_args, context)
    except Exception as ex:
        raise ex
    else:
        print(f'{indent}调用结果: {func_result}')
        print(f'{indent}响应内容: {func_result.json()}')  # todo remove
        context['response'] = func_result  # todo remove
        result[stage_index][step_index][func_hook] = func_result


def pop_pre_post(func_args):
    _pre = None
    _post = None
    if isinstance(func_args, dict):
        if '_pre' in func_args:
            _pre = func_args.pop('_pre')
        if '_post' in func_args:
            _post = func_args.pop('_post')
    return _pre, _post


def parse_func(func_hook, context):
    functions = context.get('functions', {})
    if '.' not in func_hook:
        func = functions.get(func_hook)
    else:
        func_path = func_hook.split('.')
        func_base = functions.get(func_path[0])
        if not func_base:
            raise ValueError(f'找不到指定的hook方法: {func_base}')

        func = func_base

        for attr in func_path[1:]:
            if not hasattr(func, attr):
                raise ValueError('func没有属性attr')
            func = getattr(func, attr)

    if not callable(func):
        raise TypeError(f'func: {func} 不是callable')
    return func

def do_pre(_pre, context):
    if not _pre:
        return
    indent = ' ' * 4
    print(f'{indent}执行pre', _pre)


def do_post(_post, context):
    if not _post:
        return
    indent = ' ' * 4
    print(f'{indent}执行post', _post)
    if not isinstance(_post, list):
        raise TypeError('_post应为列表格式')

    for step in _post:  # todo 合并
        if not isinstance(step, dict):
            raise TypeError('step只支持字典格式')

        for func_hook, func_args in step.items():
            indent = ' ' * 6
            print(f'{indent}解析函数: {func_hook} 参数: {func_args}')

            context['func_hook'] = func_hook

            func = parse_func(func_hook, context)
            func_args = parse_func_args(func_args, context)

            do_func(func, func_args, context)


def do_step(step, context):

    if not isinstance(step, dict):
        raise TypeError('step只支持字典格式')

    stage_index = context.get('stage_index', 0)
    step_index = context.get('step_index', 0)
    indent = ' ' * 4
    print(f'{indent}执行step: {stage_index+1}.{step_index+1}')

    context['result'][stage_index].append({})

    for func_hook, func_args in step.items():
        indent = ' ' * 6
        print(f'{indent}解析函数: {func_hook} 参数: {func_args}')

        context['func_hook'] = func_hook

        func = parse_func(func_hook, context)
        func_args = parse_func_args(func_args, context)
        _pre, _post = pop_pre_post(func_args)

        do_pre(_pre, context)
        do_func(func, func_args, context)
        do_post(_post, context)


def do_steps(steps, context):
    if not isinstance(steps, list):
        raise TypeError('steps只支持列表格式')

    for step_index, step in enumerate(steps):
        context['step_index'] = step_index
        do_step(step, context)


def do_stage(stage, context):
    stage_index = context.get('stage_index')
    indent = ' ' * 2
    print(f'{indent}执行stage: {stage_index+1}')

    context['result'].append([])

    steps = stage.get('steps', [])
    do_steps(steps, context)


def do_stages(stages, context):
    if not isinstance(stages, list):
        raise TypeError('steps只支持列表格式')

    for stage_index, stage in enumerate(stages):
        context['stage_index'] = stage_index
        do_stage(stage, context)


def main(data):
    name = data.get('name')
    functions = dict(request=request)

    # defaults = dict(env=os.environ)
    defaults = dict()
    args = dict(username='abc', password=123)
    variables = data.get('variables', {})
    # values = ChainMap(args, variables, defaults)
    result = []
    context = locals()

    stages = data.get('stages', [])
    print(f'执行pipline: {name}')
    do_stages(stages, context)
    return context['result']


if __name__ == '__main__':
    with open('/Users/apple/Documents/Projects/Self/StepRunner/httpbird/httpbird/pipline.yaml',
              encoding='utf-8') as f:
        data = yaml.safe_load(f)

    main(data)
