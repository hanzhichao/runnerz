import os
import unittest
import re
from collections import ChainMap
import threading

import ddt
from parserz import parser
from logz import log as logging
from htmlrunner import HTMLRunner

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

    def run_suite(self, suite):
        logging.info('运行Suite', suite)
        if suite._config:
            logging.info('注册Suite.config')
            self._context.register_config(suite._config)

        if suite._variables:  # 优先级高于config.variales
            logging.info('注册Suite.varaible')
            self._context.register_variables(suite._variables)

        for case in suite._cases:
            self.run_case(case)

    def run_case(self, case):
        skip, reason = self._should_skip(case)
        if skip:
            logging.info(f'跳过Case {case} {reason}')
            return
        logging.info(f'运行Case {case}')
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

    def _should_skip(self, obj: (models.Step, models.Case)):
        skip = obj._skip
        if isinstance(skip, bool):
            return skip, f'skip={skip}'

        if isinstance(skip, str):
            expr = skip
            parsed_expr = self._context.parse(expr)
            try:
                skip = eval(parsed_expr, {}, {})
            except Exception as ex:
                logging.exception(ex)
                reason = f'skip表达式 {skip} 出错'
                logging.info('跳过步骤:', obj._name, reason)
                return True
        if skip:
            reason = f'skip={parsed_expr}'
            logging.info('跳过步骤:', obj._name, reason)
            return True, reason
        return False, 'skip=False'

    def _get_step_target_function(self, step):
        _target = step._target
        ensure_type(_target, str)
        function = self._context.get_function(_target)
        kwargs = self._context.parse(step._kwargs)
        return function, kwargs

    def _run_step(self, step):
        function, kwargs = self._get_step_target_function(step)

        result = function(kwargs, self._context)  # todo 每个函数需要两个变量
        if step._extract:
            self.do_extract(step._extract)
        if step._validate:
            self.do_validate(step._validate)

        return result

    def _run_step_in_threads(self, step, concurrency):
        """一批多线程运行"""
        threads = [Thread(self._run_step, step) for i in range(concurrency)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return [t.result for t in threads]

    def _run_step_with_times(self, step, times: int):
        """多轮运行"""
        ensure_type(times, int)
        results = []
        for i in range(times):
            logging.info(f'运行Step {step} 第{i + 1}轮')
            results.append(self._run_step(step))
        return results

    def _run_step_with_concurrency(self, step, times: int, concurrency: int):
        """多轮多线程并发运行"""
        ensure_type(times, int)
        ensure_type(concurrency, int)
        results = []
        times = times // concurrency
        for i in range(times):
            logging.info(f'运行Step {step} 第{i + 1}轮 并发数: {concurrency}')
            results.extend(self._run_step_in_threads(step, concurrency))

        mod = times % concurrency  # 余数
        if mod:
            logging.info(f'运行Step {step} 第{times + 1}轮 并发数: {mod}')
            results.extend(self._run_step_in_threads(step, mod))
        return results

    def run_step(self, step):
        skip, reason = self._should_skip(step)
        if skip:
            logging.info(f'跳过Step {step} {reason}')
            return

        times = step._times
        concurrency = step._concurrency

        # 1. 无times, 只执行一次
        if not times:
            logging.info(f'运行Step {step}')
            return self._run_step(step)

        # 3. 有times, 无concurrency, 顺序执行多轮
        if not concurrency:
            return self._run_step_with_times(step, times)

        # 3. 有times和concurrency
        return self._run_step_with_concurrency(step, times, concurrency)


class UnittestRunner(Runner):
    def run_case(self, case):  # 重新run_case
        skip, reason = self._should_skip(case)
        if skip:
            raise unittest.SkipTest(f'跳过Case: {case} {reason}')
        logging.info(' 运行Case', case)
        for step in case._steps:
            self.run_step(step)

    def build_case(self, index: int, case: models.Case):
        run_case = self.run_case

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
        context = self._context
        class TestClass(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                nonlocal context
                logging.info('运行Suite', suite)
                if suite._config:
                    logging.info('注册Suite.config')
                    context.register_config(suite._config)

        for index, case in enumerate(suite._cases):
            test_method = self.build_case(index, case)
            setattr(TestClass, f'test_method_{index + 1}', test_method)

        # TestClass = ddt.ddt(TestClass)
        TestClass.__doc__ = suite._name # suite名

        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestClass)
        return test_suite

    def run(self, suite):
        test_suite = self.build_suite(suite)
        # runner = unittest.TextTestRunner(verbosity=2)
        runner = HTMLRunner()
        result = runner.run(test_suite)
        return result