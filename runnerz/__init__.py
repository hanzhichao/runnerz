import os
from string import Template
from collections import ChainMap
import threading
from concurrent.futures import ThreadPoolExecutor
import random

import yaml
import requests


# 步骤定义
CONFIG = 'config'  # 配置关键字  settings
STAGES = 'stages'
STEPS = 'steps'  # 步骤关键字  steps/teststeps/testcases

NAME = 'name'  # 名称
VAIABLES = 'variables'  # 用户自定义变量关键字
BASEURL = 'baseurl'
REQUEST = 'request'  # 请求配置,请求数据关键字
CHECK = 'verify'  # 验证关键字  check/validate/assert
EXTRACT = 'extract'   # 提取关键字 output/register
SKIP = 'skip'  # 跳过步骤关键字
TIMES = 'times'  # 循环步骤关键字  circle
ACTION = 'action'  # 步骤类型 operation/keywords/function/target
RUN_TYPE = 'run_type'  # 运行方式

# 上下文变量
POLL = '_poll'
SESSION = '_session'  # 请求会话


class Step(object):
    def __init__(self, step, config, context):
        self.step = step
        self.config = config
        self.context = context

        self.name = step.get(NAME)
        self.skip = step.get(SKIP)
        self.times = step.get(TIMES, 1)
        self.run_type = step.get(RUN_TYPE)
        self.check = step.get(CHECK)
        self.extract = step.get(EXTRACT)

    def parse(self, data):
        data_str = yaml.dump(data, default_flow_style=False)  # 先转为字符串
        if '$' in data_str:
            data_str = Template(data_str).safe_substitute(self.context)  # 替换${变量}为varables中的同名变量
            data = yaml.safe_load(data_str)  # 重新转为字典
        return data

    def check(self):
        # 处理断言
        if self.check:
            for line in self.check:
                result = eval(line, {}, self.context)  # 计算断言表达式，True代表成功，False代表失败
                print("   处理断言:", line, "结果:", "PASS" if result else "FAIL")

    def extract(self):
        for key, value in self.extract.items():
            # 计算value表达式，可使用的全局变量为空，可使用的局部变量为RESPONSE(响应对象)
            result = eval(value, {}, self.context)  # 保存变量结果到上下文中
            print("   提取变量:", key, value, "结果:", result)
            self.context[key] = result

    def parallel_run(self):
        # poll = self.context.get(POLL)

        # print(poll)
        def run_times(i):
            print('  执行步骤:', self.name, f'第{i+1}轮' if self.times > 1 else '')
            self.process()

        for i in range(self.times):
            t = threading.Thread(target=run_times(i), args=(i,))
            t.start()
            t.join()
        # results = [poll.submit(run_times, i) for i in range(self.times)]
        # print(results)
        # return results

    def sequence_run(self):
        for i in range(self.times):
            print('  执行步骤:', self.name, f'第{i+1}轮' if self.times > 1 else '')
            self.process()

    def run(self):
        if self.skip:
            print('  跳过步骤:', self.name)
            return
        # print('  执行步骤:', self.name)
        if self.run_type == 'parallel':
            return self.parallel_run()
        else:
            return self.sequence_run()

    def process(self):
        pass


class Http(Step):
    def __init__(self, step, config, context):
        super().__init__(step, config, context)
        self.baseurl = config.get(BASEURL)
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

        # 注册上下文变量
        step_result = dict(
            request=request,
            response=response,
            result=response,
            status_code=response.status_code,
            response_text=response.text,
            response_headers=response.headers,
            response_time=response.elapsed.seconds
        )
        self.context['steps'].append(step_result)  # 保存步骤结果
        self.context.update(step_result)  # 将最近的响应结果更新到上下文变量中

    def process(self):
        request = self.step.get(REQUEST)
        request = self.parse(request)
        self.set_default_method(request)
        self.pack_url(request)
        self.send_request(request)


class Stage(object):  # steps
    def __init__(self, stage, config, context):
        self.stage = stage
        self.config = config
        self.context = context

        self.name = stage.get(NAME)
        self.run_type = stage.get(RUN_TYPE)
        self.steps = stage.get(STEPS)
        self.context['steps'] = []

    def parallel_run(self):
        self.context.setdefault(POLL, ThreadPoolExecutor(max_workers=len(self.steps)))
        poll = self.context.get(POLL)

        def run_step(step):
            print('run step')
            Http(step, self.config, self.context).run()
        results = [poll.submit(run_step, step) for step in self.steps]
        return results

    def sequence_run(self):
        for step in self.steps:
            Http(step, self.config, self.context).run()

    def run(self):
        print(' 执行stage:', self.name, '运行方式:', self.run_type)
        if self.run_type == 'parallel':
            return self.parallel_run()
        elif self.run_type == 'random':
            random.shuffle(self.steps)

        return self.sequence_run()


class Flow(object):
    def __init__(self, data):
        self.data = data
        self.config = data.get(CONFIG, {})
        self.name = self.config.get(NAME)
        self.variables = self.config.get(VAIABLES, {})
        self.context = ChainMap(self.variables, os.environ)

    def run(self):
        print('执行流程:', self.name)
        stages = data.get(STAGES)
        for stage in stages:
            Stage(stage, self.config, self.context).run()


if __name__ == "__main__":
    with open('/Users/apple/Documents/Projects/stepz/stepz/data.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    Flow(data).run()
