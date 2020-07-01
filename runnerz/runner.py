import os
import unittest
import re
from collections import ChainMap
import threading
from copy import deepcopy

import ddt
from parserz import parser
from logz import log as logging
from htmlrunner import HTMLRunner
from filez import file

from runnerz.utils.ensurez import ensure_type
from runnerz.actions import BUILD_IN_FUNCTIONS, COMPARE_FUNCS
from runnerz import models

FUNCTION_REGEX = re.compile(r'\${(?P<func>.*?)}')
CSV_REGEX = re.compile(r'\${P\((?P<csv>.*?)\)}')

# logging.level = 'info'


class Thread(threading.Thread):
    def __init__(self, func, *args, **kwargs):  # 改变线程的使用方式，可以直接传递函数方法和函数参数
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)  # 为线程添加属性result存储运行结果


class Result(object):
    pass


class Context(object):
    def __init__(self):
        self._variables = ChainMap({}, os.environ)
        self._functions = BUILD_IN_FUNCTIONS
        self._config = {}

    def dot_get(self, expr: str):
        """解析并获取变量值, expr: $a"""
        ensure_type(expr, str)
        return parser.dot_get(expr, self._variables)

    def parse(self, data: (str, list, dict)):
        return parser.parse(data, self._variables)

    def get_function(self, target: str):
        return self._functions.get(target)

    def register_functions(self, functions: dict):
        self._functions.update(functions)

    def register_variables(self, variables: dict):
        ensure_type(variables, dict)
        self._variables.update(variables)

    def register_config(self, config: dict):
        ensure_type(config, dict)
        if 'variables' in config:
            _variables = config.pop('variables')
            ensure_type(_variables, dict)
            self.register_variables(_variables)
        self._config.update(config)

    def __repr__(self):
        return '<Context variables: %s functions: %s config: %s' % (self._variables, self._functions, self._config)


class Runner(object):
    def __init__(self):
        self._context = Context()

    def _register_keyword(self, keyword: models.Keyword):
        key = keyword._key
        docs = keyword._docs
        arg_names = keyword._args
        steps = keyword._steps
        func_return = keyword._return
        run_step = self.run_step

        def func(kwargs, context):
            if isinstance(kwargs, list):
                kwargs = dict(zip(arg_names, kwargs))

            context = deepcopy(self._context)  # deepcopy以不影响原上下文
            context.register_variables(kwargs)

            for step in steps:
                run_step(step, context)
            return locals().get(func_return)  # todo return $a, $b

        func.__name__ = key
        func.__doc__ = docs
        self._context.register_functions({key: func})

    def _register_suite(self, suite):
        if suite._config:
            logging.info('注册Suite.config')
            self._context.register_config(suite._config)
        if suite._variables:  # 优先级高于config.variales
            logging.info('注册Suite.varaible')
            self._context.register_variables(suite._variables)

        if suite._keywords:
            logging.info('注册Suite.keywords')
            [self._register_keyword(keyword) for keyword in suite._keywords]

    def run_suite(self, suite):
        self._register_suite(suite)
        logging.info('运行Suite', suite)
        for case in suite._cases:
            self.run_case(case)

    def run_case(self, case, context=None):
        context = context or self._context
        skip, reason = self._should_skip(case, context)
        if skip:
            logging.info(f' 跳过Case {case} {reason}')
            return
        logging.info(f' 运行Case {case}')
        for step in case._steps:
            self.run_step(step)

    def do_extract(self, extract: list):
        """处理提取变量"""
        for line in extract:
            logging.info(f'  提取变量: {line}')
            key, expr = tuple(line.items())[0]
            ensure_type(expr, str)
            ensure_type(key, str)
            value = self._context.dot_get(expr)
            logging.info(f'  注册变量: {key}={value}')
            self._context.register_variables({key: value})

    def do_validate(self, validate):
        """处理断言"""
        for line in validate:
            logging.info(f'  处理断言: {line}')
            if 'comparator' in line:
                comparator = line.get('comparator')
                check = line.get('check')
                expect = line.get('expect')
            else:
                comparator, value = tuple(line.items())[0]
                check, expect = value
            compare_func = COMPARE_FUNCS.get(comparator)
            field = self._context.dot_get(check.strip('.'))
            assert compare_func(field, expect), f'表达式: {check} 实际结果: {field} not {comparator} 期望结果: {expect}'

    @staticmethod
    def _parse_parameters(parameters: list) -> tuple:
        """解析parameters中的变量和数据"""
        line = parameters[0]
        keys, data = tuple(line.items())[0]
        if isinstance(data, str):
            matched = re.match(CSV_REGEX, data)
            if not matched:
                raise ValueError(f'参数化不支持: {data} 形式')
            csv_file = matched.group('csv')
            data = file.load(csv_file)
            data = data[1:]  # 舍弃标题行
        keys = keys.split('-')
        return keys, data

    def _should_skip(self, obj: (models.Step, models.Case), context):
        skip = obj._skip
        if not isinstance(skip, str):
            skip = True if skip else False
            return skip, f'skip={skip}'

        if isinstance(skip, str):
            expr = skip
            parsed_expr = context.parse(expr)
            try:
                skip = eval(parsed_expr, {}, {})
            except Exception as ex:
                logging.exception(ex)
                reason = f'skip表达式 {skip} 出错'
                return True, reason
            if skip:
                reason = f'skip={parsed_expr}'
                return True, reason
        return False, 'skip=False'

    def _get_step_target_function(self, step):
        _target = step._target
        ensure_type(_target, str)
        function = self._context.get_function(_target)
        kwargs = self._context.parse(step._kwargs)
        return function, kwargs

    def _run_step(self, step, context):
        function, kwargs = self._get_step_target_function(step)

        result = function(kwargs, context)  # todo 每个函数需要两个变量
        if step._extract:
            self.do_extract(step._extract)
        if step._validate:
            self.do_validate(step._validate)

        return result

    def _run_step_in_threads(self, step, concurrency, context):
        """一批多线程运行"""
        threads = [Thread(self._run_step, step, context) for i in range(concurrency)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return [t.result for t in threads]

    def _run_step_with_times(self, step, times: int, context):
        """多轮运行"""
        ensure_type(times, int)
        results = []
        for i in range(times):
            logging.info(f'  运行Step {step} 第{i + 1}轮')
            results.append(self._run_step(step, context))
        return results

    def _run_step_with_concurrency(self, step, times: int, concurrency: int, context):
        """多轮多线程并发运行"""
        ensure_type(times, int)
        ensure_type(concurrency, int)
        results = []
        times = times // concurrency
        for i in range(times):
            logging.info(f'  运行Step {step} 第{i + 1}轮 并发数: {concurrency}')
            results.extend(self._run_step_in_threads(step, concurrency, context))

        mod = times % concurrency  # 余数
        if mod:
            logging.info(f'运行Step {step} 第{times + 1}轮 并发数: {mod}')
            results.extend(self._run_step_in_threads(step, mod, context))
        return results

    def run_step(self, step: models.Step, context=None):
        context = context or self._context
        skip, reason = self._should_skip(step, context)
        if skip:
            logging.info(f'  跳过Step {step} {reason}')
            return

        times = step._times
        concurrency = step._concurrency

        # 1. 无times, 只执行一次
        if not times:
            logging.info(f'  运行Step {step}')
            return self._run_step(step, context)

        # 3. 有times, 无concurrency, 顺序执行多轮
        if not concurrency:
            return self._run_step_with_times(step, times, context)

        # 3. 有times和concurrency
        return self._run_step_with_concurrency(step, times, concurrency, context)


class UnittestRunner(Runner):
    def run_case(self, case, context=None):  # 重新run_case
        context = context or self._context
        skip, reason = self._should_skip(case, context)
        if skip:
            raise unittest.SkipTest(f'跳过Case: {case} {reason}')
        logging.info(' 运行Case', case)
        for step in case._steps:
            self.run_step(step)

    def build_case(self, index: int, case: models.Case):
        run_case = self.run_case
        context = self._context
        parameters = case._parameters
        if parameters:
            keys, data = self._parse_parameters(parameters)

            def _test_method(self, values):
                nonlocal case
                nonlocal context

                key_values = dict(zip(keys, values))
                context.register_variables(key_values)
                run_case(case)
            test_method = ddt.data(*data)(_test_method)
        else:
            def _test_method(self):
                nonlocal case
                run_case(case)
            test_method = _test_method

        test_method.__name__ = f'test_method_{index + 1}'
        test_method.__doc__ = test_method.name = case._name
        test_method.tags = case._tags
        test_method.level = case._level
        return test_method

    def build_suite(self, suite: models.Suite) -> unittest.TestSuite:
        """组装suite"""

        class TestClass(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                self._register_suite(suite)
                logging.info('运行Suite', suite)

        for index, case in enumerate(suite._cases):
            test_method = self.build_case(index, case)
            setattr(TestClass, f'test_method_{index + 1}', test_method)

        TestClass = ddt.ddt(TestClass)
        TestClass.__doc__ = suite._name # suite名

        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestClass)
        return test_suite

    def run_suite(self, suite: models.Suite):
        test_suite = self.build_suite(suite)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        return result


class HTMLTestRunner(UnittestRunner):
    def run_suite(self, suite: models.Suite):
        test_suite = self.build_suite(suite)
        runner = HTMLRunner()
        result = runner.run(test_suite)
        return result