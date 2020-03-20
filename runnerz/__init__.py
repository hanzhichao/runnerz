import os
from string import Template
from collections import ChainMap
import threading
# from concurrent.futures import ThreadPoolExecutor
import random
import re
import json
import operator

import yaml
import requests
from jsonpath import jsonpath
from lxml import etree
from lxml.etree import HTMLParser

from logz import log

log.format = '%(asctime)s %(threadName)s %(levelname)s %(message)s'
print = log.info

# 步骤定义
CONFIG = 'config'  # 配置关键字  settings
STAGES = 'stages'
STEPS = 'steps'  # 步骤关键字  steps/teststeps/testcases

NAME = 'name'  # 名称
VAIABLES = 'variables'  # 用户自定义变量关键字
RUN_TYPE = 'run_type'  # stage中steps运行方式
BASEURL = 'baseurl'
REQUEST = 'request'  # 请求配置,请求数据关键字
CHECK = 'check'  # 验证关键字  check/validate/assert
EXTRACT = 'extract'   # 提取关键字 output/register
SKIP = 'skip'  # 跳过步骤关键字
TIMES = 'times'  # 循环步骤关键字  circle
ACTION = 'action'  # 步骤类型 operation/keywords/function/target

CONCURRENCY = 'concurrency'

# 上下文变量
POLL = '_poll'  # 线程池  废弃
SESSION = '_session'  # 请求会话
CONFIG = '_config'  # 配置


class MyThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):  # 改变线程的使用方式，可以直接传递函数方法和函数参数
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)  # 为线程添加属性result存储运行结果


def find_by_jsonpath(text, expr):
    try:
        res_dict = json.loads(text)
    except Exception as ex:
        log.exception(ex)
        return
    result = jsonpath(res_dict, expr)
    if result and len(result) == 1:
        return result[0]
    return result


def find_by_re(text, expr):
    result = re.findall(expr, text)
    if result and len(result) == 1:
        return result[0]
    return result


def find_by_xpath(text, expr):
    try:
        html = etree.HTML(text, etree.HTMLParser())
        result = html.xpath('expr')
    except Exception:
        result = False
    if result and len(result) == 1:
        return result[0]
    return result


class Base(object):  # 节点通用
    def __init__(self, data, context={}):
        self.data = data
        self.context = context
        self.name = data.get(NAME)
        self.skip = data.get(SKIP)
        self.config = context.get(CONFIG)
        self.result = None
        self.status = None

    def _run(self):
        pass

    def _post(self):
        pass

    def process(self):
        pass

    def run(self):
        try:
            self.result = self._run()
        except AssertionError as ex:
            # log.exception(ex)
            self.status = 'FAIL'
            raise ex
        except Exception as ex:
            # log.exception(ex)
            self.status = 'ERROR'
            raise ex
        else:
            self.status = 'PASS'
        return self.result


class Step(Base):
    def __init__(self, step, context):
        super().__init__(step, context)
        self.step = self.data

        self.times = step.get(TIMES, 1)
        self.run_type = step.get(RUN_TYPE)
        self.check = step.get(CHECK)
        self.extract = step.get(EXTRACT)
        self.concurrency = step.get(CONCURRENCY, 1)

    def parse(self, data):
        data_str = yaml.dump(data, default_flow_style=False)  # 先转为字符串
        if '$' in data_str:
            data_str = Template(data_str).safe_substitute(self.context)  # 替换${变量}为varables中的同名变量
            data = yaml.safe_load(data_str)  # 重新转为字典
        return data

    def post_check(self):
        # 处理断言
        results = []
        for line in self.check:
            if isinstance(line, str):
                result = eval(line, {}, self.context)  # 计算断言表达式，True代表成功，False代表失败
            elif isinstance(line, dict):
                for key, value in line.items():
                    if hasattr(operator, key):
                        func = getattr(operator, key)
                        items = []
                        for item in value:
                            if isinstance(item, str):
                                item = self.context.get(item, item)
                            items.append(item)

                        result = func(*items)
            print("   处理断言:", line, "结果:", "PASS" if result else "FAIL")
            results.append(result)
        if not all(results):
            raise AssertionError('断言失败')

    def post_extract(self):
        for key, value in self.extract.items():
            # 计算value表达式，可使用的全局变量为空，可使用的局部变量为RESPONSE(响应对象)
            result = eval(value, {}, self.context)  # 保存变量结果到上下文中
            print("   提取变量:", key, value, "结果:", result)
            self.context[key] = result

    def parallel_run(self):
        times = self.times // self.concurrency
        results = []
        for i in range(times):
            print('  执行步骤:', self.name, f'第{i+1}轮 并发量: {self.concurrency}' if self.times > 1 else '')

            threads = [MyThread(self.process) for i in range(self.concurrency)]
            [t.start() for t in threads]
            [t.join() for t in threads]
            results.extend([t.result for t in threads])

    def sequence_run(self):
        results = []
        for i in range(self.times):
            print('  执行步骤:', self.name, f'第{i+1}轮' if self.times > 1 else '')
            result = self.process()
            results.append(result)
            self.context['result'] = self.result
        return results

    def _run(self):
        if self.skip:
            print('  跳过步骤:', self.name)
            return
        if self.concurrency > 1:
            result = self.parallel_run()
        else:
            result = self.sequence_run()


        if self.check:
            self.post_check()

        if self.extract:
            self.post_extract()
        return result

    def process(self):
        pass


class Http(Step):
    def __init__(self, step, context):
        super().__init__(step, context)
        self.baseurl = self.config.get(BASEURL)
        context.setdefault(SESSION, requests.session())
        self.session = context.get(SESSION)

        request = self.config.get(REQUEST)
        if request:
            for key, value in request.items():
                self.session.__setattr__(key, value)

    def set_default_method(self, request):
        if request.get('data') or request.get('json') or request.get('files'):
            request.setdefault('method', 'post')
        else:
            request.setdefault('method', 'get')

    def pack_url(self, request):
        if not self.baseurl:
            return
        url = request.get('url')
        if not url.startswith('http'):
            request['url'] = '/'.join((self.baseurl.rstrip('/'), url.lstrip('/')))

    def send_request(self, request):
        # 发送请求
        print('   请求url:', request.get('url'))  # print(' 发送请求:', request)
        response = self.session.request(**request)  # 字典解包，发送接口
        print('   状态码:', response.status_code)  # print(' 响应数据:', response.text)

        try:
            res_dict = response.json()
        except Exception:
            res_dict = {}

        # 注册上下文变量
        step_result = dict(
            request=request,
            response=response,
            response_json=res_dict,
            status_code=response.status_code,
            response_text=response.text,
            response_headers=response.headers,
            response_time=response.elapsed.seconds,
            xpath=lambda expr: find_by_xpath(response.text, expr),
            jsonpath=lambda expr: find_by_jsonpath(response.text, expr),
            re=lambda expr: find_by_re(response.text, expr)
        )
        self.context['steps'].append(step_result)  # 保存步骤结果
        self.context.update(step_result)  # 将最近的响应结果更新到上下文变量中
        return response

    def process(self):
        request = self.step.get(REQUEST)
        request = self.parse(request)
        self.set_default_method(request)
        self.pack_url(request)
        return self.send_request(request)


class Stage(Base):  # steps
    def __init__(self, stage, context):
        super().__init__(data, context)
        self.stage = stage
        self.run_type = stage.get(RUN_TYPE)
        self.steps = stage.get(STEPS)
        self.context['steps'] = []

    def parallel_run(self):
        threads = []
        results = []
        for step in self.steps:
            action = Http(step, self.context)
            threads.append(MyThread(action.run))
        [t.start() for t in threads]
        [t.join() for t in threads]
        results.extend([t.result for t in threads])
        return results

    def sequence_run(self):
        results = []
        for step in self.steps:
            result = Http(step, self.context).run()
            results.append(result)
        return results

    def _run(self):
        print(' 执行stage:', self.name, '运行方式:', self.run_type)
        if self.run_type == 'parallel':
            return self.parallel_run()
        elif self.run_type == 'random':
            random.shuffle(self.steps)
        return self.sequence_run()


class Flow(Base):
    def __init__(self, data, context={}):
        super().__init__(data, context)
        self.config = data.get(CONFIG, {})

        self.variables = self.config.get(VAIABLES, {})
        self.context = ChainMap(self.variables, os.environ)
        self.context[CONFIG] = self.config

    def _run(self):
        print('执行流程:', self.name)
        stages = data.get(STAGES)
        results = []
        for stage in stages:
            result = Stage(stage, self.context).run()
            results.append(result)
        return results

    def run(self):
        try:
            self.result = self._run()
        except AssertionError as ex:
            log.exception(ex)
            self.status = 'FAIL'
        except Exception as ex:
            log.exception(ex)
            self.status = 'ERROR'
        else:
            self.status = 'PASS'
        return self.result


if __name__ == "__main__":
    with open('/Users/apple/Documents/Projects/Self/PyPi/runnerz/data.yml', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    f = Flow(data)
    print(f.run())
    print(f.status)
    print(f.result)
