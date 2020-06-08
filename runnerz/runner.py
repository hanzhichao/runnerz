import re
import json
import requests
from string import Template
from functools import reduce
from operator import eq, gt, lt, ge, le
import unittest
import ddt
import importlib
import types
import time
import platform

from logz import log  # 需要 pip install logz
from filez import file # 需要 pip install filez

print = log.info


COMPARE_FUNCS = dict(
    eq=eq, gt=gt, lt=lt, ge=ge, le=le,
    len_eq=lambda x, y: len(x) == len(y),
    str_eq=lambda x, y: str(x) == str(y),
    type_match=lambda x, y: isinstance(x, y),
    regex_match=lambda x, y: re.match(y, x)
)

FUNCTION_REGEX = re.compile(r'\${(?P<func>.*?)}')
CSV_REGEXT = re.compile(r'\${P\((?P<csv>.*?)\)}')


def do_dot(item, key: str):
    """单个content.url取值"""
    if hasattr(item, key):
        return getattr(item, key)
    if key.isdigit():
        key = int(key)
    try:
        return item[key]
    except Exception as ex:
        log.exception(ex)
        return None


def get_field(context: dict, expr: str):
    """解析形如content.result.0.id的取值"""
    if '.' in expr:
        value = expr.split('.')
        field = context.get(value[0])
        return reduce(lambda x, y: do_dot(x, y), value[1:], field)
    else:
        return context.get(expr)


def parse_request(base_url: str, request: dict) -> dict:
    """补充完整request"""
    if base_url and not request['url'].startswith('http'):
        request['url'] = base_url + request['url']
    return request


def send_request(context, session, request):
    """发送请求"""
    response = session.request(**request)
    print('请求数据', request)
    print('响应数据', response.text)
    try:
        content = response.json()
    except json.decoder.JSONDecodeError:
        content = {}

    # 注册上下文变量
    context.update(
        response=response,
        request=response.request,
        content=content,
        status_code=response.status_code,
        headers=response.headers,
        ok=response.ok,
        reason=response.reason,
        response_time=response.elapsed.mileseconds
    )


def do_extract(context: dict, extract: list):
    """处理提取变量"""
    for line in extract:
        key, value = tuple(line.items())[0]
        context[key] = get_field(context, value)


def do_validate(context, validate):
    """处理断言"""
    for line in validate:
        if 'comparator' in line:
            comparator = line.get('comparator')
            check = line.get('check')
            expect = line.get('expect')
        else:
            comparator, value = tuple(line.items())[0]
            check, expect = value
        compare_func = COMPARE_FUNCS.get(comparator)
        field = get_field(context, check)
        assert compare_func(field, expect), f'表达式: {check} 实际结果: {field} not {comparator} 期望结果: {expect}'


def get_functions() -> dict:
    """从debugtalk模块中获取功能函数"""
    module = importlib.import_module('debugtalk')
    functions = {key: value for key, value in module.__dict__.items()
                 if not key.startswith('__') and callable(value)}
    return functions


def parse_dollar(context: dict, data: (list,dict)) -> (list, dict):
    """解析$变量"""
    data_str = json.dumps(data)
    if '$' in data_str:
        data_str = Template(data_str).safe_substitute(context)
        return json.loads(data_str)
    else:
        return data


def do_test_steps(self, steps: list):
    pass


def do_test(self, test: dict) -> None:
    """测试用例运行方法"""
    if test.get('skip'):
        raise unittest.SkipTest
    setup_hooks = test.get('setup_hooks')
    teardown_hooks = test.get('teardown_hooks')
    parsed_test = parse_dollar(self.context, test)
    request = parse_request(self.base_url, parsed_test.get('request'))
    self.context['request'] = request  # 注册上下文以方便setup_hooks中的方法可以使用

    if setup_hooks:
        parse_function(self.context, self.functions, setup_hooks)
    if teardown_hooks:
        self.addCleanup(parse_function, self.context, self.functions, teardown_hooks)

    send_request(self.context, self.session, request)
    do_extract(self.context, parsed_test.get('extract', []))
    do_validate(self.context, parsed_test.get('validate', []))


def parse_function(context: dict, functions: dict, data: (list, dict)) -> (list,dict):
    data_str = json.dumps(data)
    if '$' in data_str:
        data_str = Template(data_str).safe_substitute(context)

    def repr_func(matched):
        """自定义re.sub替换方法"""
        if not matched:
            return
        return str(eval(matched.group(1), {}, functions))

    data_str = re.sub(FUNCTION_REGEX, repr_func, data_str)
    return json.loads(data_str)


def parse_parameters(parameters: list) -> tuple:
    """解析parameters中的变量和数据"""
    line = parameters[0]
    keys, data = tuple(line.items())[0]
    if isinstance(data, str):
        matched = re.match(CSV_REGEXT, data)
        if not matched:
            raise ValueError(f'参数化不支持: {data} 形式')
        csv_file = matched.group('csv')
        data = file.load(csv_file)
        data = data[1:]  # 舍弃标题行
        print('数据', data)
    keys = keys.split('-')
    return keys, data


def build_case(index: int, test: dict) -> types.FunctionType:
    """生成用例方法"""
    parameters = test.get('parameters')
    if parameters:
        keys, data = parse_parameters(parameters)

        def test_api_ddt(self, values):
            key_values = dict(zip(keys, values))
            print('测试数据', key_values)
            self.context.update(key_values)
            do_test(self, test)

        test_method = ddt.data(*data)(test_api_ddt)
    else:
        def test_api(self):
            do_test(self, test)

        test_method = test_api

    test_method.__name__ = f'test_api_{index+1}'
    test_method.__doc__ = test.get("name")
    return test_method


def format_data(data: list)-> dict:
    """将[config, test, test]格式改为{name, config, testcases格式}"""
    config = data[0].get('config')
    name = config.pop('name')
    testcases = [test.get('test') for test in data[1:]]
    return dict(name=name, config=config, testcases=testcases)


def build_suite(data: (list, dict), functions=None)-> unittest.TestSuite:
    if isinstance(data, list):
        data = format_data(data)
    name = data.get('name', '')
    config = data.get('config', {})
    testcases = data.get('testcases', [])

    """组装suite"""
    class TestApi(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            nonlocal config
            cls.functions = functions or {}
            cls.session = requests.session()

            context = config.get('variables')
            config = parse_function(context, cls.functions, config)
            config_request = config.get('request')
            cls.base_url = config_request.pop('base_url') if 'base_url' in config_request else None
            cls.context = config.get('variables', {})
            for key, value in config_request.items():
                setattr(cls.session, key, value)

    for index, test in enumerate(testcases):
        # test = test.get('test')
        test_method = build_case(index, test)
        setattr(TestApi, f'test_api_{index+1}', test_method)

    TestApi = ddt.ddt(TestApi)
    TestApi.__doc__ = name

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestApi)
    return suite


class RunnerResult(unittest.TestResult):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = None
        self.base_url = None
        self.start_at = None
        self.end_at = None
        self.successes = []
        self.output = []
        self.records = []

    def startTest(self, test):
        if self.start_at is None:
            self.start_at = time.time()
            self.name = test.__doc__
            self.base_url = getattr(test, 'base_url')
        else:  # 保存上一次的结果
            context = getattr(test, 'context', {})
            request = context.get('request')
            response = dict(status_code=context.get('status_code'),
                            content=context.get('content'),
                            text=context.get('text'),
                            headers=context.get('headers'),
                            response_time=context.get('response_time'))
            meta_data = dict(name=None, status=None, request=request, response=response, validators=[])
            self.records.append(dict(attachment='', meta_data=meta_data))


        super().startTest(test)

    def stopTest(self, test):
        self.end_at = time.time()
        super().stopTest(test)

    def addSuccess(self, test):
        self.successes.append(test)

    @property
    def time(self):
        return dict(start_at=self.start_at, duration=self.end_at-self.start_at)

    @property
    def success(self):
        return len(self.failures) == 0 and len(self.errors) == 0 and len(self.unexpectedSuccesses) == 0

    @property
    def stat(self):
        return dict(
            testsRun=self.testsRun,
            successes=len(self.successes),
            skipped=len(self.skipped),
            failures=len(self.failures),
            errors=len(self.errors),
            expectedFailures=len(self.expectedFailures),
            unexpectedSuccesses=len(self.unexpectedSuccesses)
        )

    @property
    def summary(self):
        return dict(name=self.name, base_url=self.base_url, success=self.success,
                    time=self.time, stat=self.stat, output=self.output, records=self.records)


def run_suite(suite: unittest.TestSuite) -> unittest.TestResult:
    """运行suite"""
    with open('result.txt', 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2, resultclass=RunnerResult)
        return runner.run(suite)


def run(data: (dict, list)) -> unittest.TestResult:
    functions = get_functions()
    suite = build_suite(data, functions)
    return run_suite(suite)


def sum_stat(results, field):
    return sum([result.summary.get('stat').get(field, 0) for result in results])


def run_multi(datas: list):
    functions = get_functions()
    suites = [build_suite(data, functions) for data in datas]
    # suite = unittest.TestSuite(suites)
    # print(suite)
    summary = {}
    start_at = time.time()
    results = [run_suite(suite) for suite in suites]

    summary['time'] = dict(start_at=start_at, duration=time.time() - start_at)
    summary['success'] = all([result.summary.get('success') for result in results])
    summary['stat'] = dict(
        testsRun=sum_stat(results, 'testsRun'),
        successes=sum_stat(results, 'successes'),
        skipped=sum_stat(results, 'skipped'),
        errors=sum_stat(results, 'errors'),
        failures=sum_stat(results, 'failures'),
        expectedFailures=sum_stat(results, 'expectedFailures'),
        unexpectedSuccesses=sum_stat(results, 'unexpectedSuccesses'),
    )
    summary['platform'] = dict(httprunner_version='1.5.6',
                               python_version=platform.python_version(),
                               platform=platform.platform())
    summary['details'] = [result.summary for result in results]
    return summary


if __name__ == '__main__':
    import os
    data_file = os.path.join(os.path.dirname(__file__), 'data.yaml')
    data = file.load(data_file)
    result = run_multi([data, data])
    from pprint import pprint
    pprint(result)