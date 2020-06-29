from parserz import parser
from logz import log as logging
from runnerz.utils.ensurez import ensure_type
from runnerz.actions import request, log
from runnerz import models
from operator import eq, gt, lt, ge, le
import re
import unittest
import ddt

logging.level = 'info'


COMPARE_FUNCS = dict(
    eq=eq, gt=gt, lt=lt, ge=ge, le=le,
    len_eq=lambda x, y: len(x) == len(y),
    str_eq=lambda x, y: str(x) == str(y),
    type_match=lambda x, y: isinstance(x, y),
    regex_match=lambda x, y: re.match(y, x)
)

BUILD_IN_FUNCTIONS = {
    'request': request,
    'log': log
}


class Result(object):
    pass


class Context(object):
    def __init__(self):
        self._variables = {}
        self._functions = {}
        self._config = {}

        self.register_functions(BUILD_IN_FUNCTIONS)

    def dot_get(self, expr: str):
        """解析并获取变量值, expr: $a"""
        ensure_type(expr, str)
        return parser.dot_get(expr, self._variables)

    def parse(self, data: (str, list, dict)):
        logging.debug('data', data)
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

        for case in suite._cases:
            self.run_case(case)

    def run_case(self, case):
        _skip = case._skip
        if _skip:
            logging.info('  跳过Case', case)
            return
        logging.info(' 运行Case', case)
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

    def run_step(self, step):
        _skip = step._skip
        if _skip:
            logging.info('  跳过Step', step)
            return

        logging.info('  运行Step', step)
        _target = step._target
        ensure_type(_target, str)
        function = self._context.get_function(_target)
        logging.debug('_target', _target, function)

        kwargs = self._context.parse(step._kwargs)
        logging.warning('kwargs', kwargs)

        result = function(kwargs, self._context)  # todo 每个函数需要两个变量
        if step._extract:
            self.do_extract(step._extract)

        if step._validate:
            self.do_validate(step._validate)


class UnittestRunner(Runner):
    def run_case(self, case):  # 重新run_case
        _skip = case._skip
        if _skip:
            raise unittest.SkipTest(f'跳过Case: {case}')
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
        logging.info('test_method_name', case._name)
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
            print(index, case)
            test_method = self.build_case(index, case)
            setattr(TestClass, f'test_method_{index + 1}', test_method)

        # TestClass = ddt.ddt(TestClass)
        TestClass.__doc__ = suite._name # suite名

        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestClass)
        return test_suite

    def run(self, suite):
        test_suite = self.build_suite(suite)
        logging.warning(test_suite)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)