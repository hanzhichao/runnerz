import os
from abc import ABCMeta, abstractmethod
from collections import ChainMap

from logz import log, logit

from runnerz.keywords import *
from runnerz.utils import merge_update, parse, get_fixtures
from runnerz.thread import MyThread


DEFAULT_VARIABLES = ChainMap({}, os.environ)
DEFAULT_FUNCTIONS = {}
DEFAULT_CONFIG = {}


class Base(object, metaclass=ABCMeta):  # 节点通用
    def __init__(self, data, context=None):
        self.raw = data

        self.name = data.get(NAME)
        self.description = data.get(DESCRIPTION)
        self.tags = data.get(TAGS)
        self.level = data.get(LEVEL)

        self.config = data.get(CONFIG, {})
        self.variables = data.get(VAIABLES, {})  # 在项目中还是config中?

        self.skip = data.get(SKIP)
        self.timeout = data.get(TIMEOUT)
        self.times = data.get(TIMES, 1)  # 3 or rerun  (3, 1, 'on_fail/on_error/always')
        self.concurrency = data.get(CONCURRENCY)

        self.result = None
        self.status = None

        self.context = context

        self.config_context(context)  # 1. 初始化上下文

        self.data = parse(data, self.context)  # 2. 数据解析
        self.setup_hooks = self.data.get(SETUP_HOOKS) or self.config.get(SETUP_HOOKS)
        self.teardown_hooks = self.data.get(TEARDOWN_HOOKS) or self.config.get(TEARDOWN_HOOKS)
        self.pre_steps = []
        self.post_steps = []
        self.handle_fixtures(self.setup_hooks, self.pre_steps)
        self.handle_fixtures(self.teardown_hooks, self.post_steps)

    def merge_config(self):
        """融合各个步骤/步骤组中的配置"""
        if self.config:
            merge_update(self.context[CONFIG], self.config)

    def merge_variables(self):
        """融合各个步骤/步骤组中的变量集合"""
        if self.config:
            config_variables = self.config.get(VAIABLES)
            if config_variables:
                self.variables.update(config_variables)
        if self.variables:
            self.context[VAIABLES].update(self.variables)

    def config_context(self, context):
        """设置上下文,获取"""

        self.context = context or {}
        self.context.setdefault(CONFIG, DEFAULT_CONFIG)

        self.context.setdefault(VAIABLES, DEFAULT_VARIABLES)
        self.context.setdefault(FUNCTIONS, DEFAULT_FUNCTIONS)
        self.context[FIXTURES] = get_fixtures()

        self.merge_config()
        self.merge_variables()

    def handle_fixtures(self, data, steps):
        fixtures = self.context.get(FIXTURES, {})
        if data:
            if not isinstance(data, list):
                raise TypeError('setup_hooks必须为list格式')
            for step in data:  # - print_me: $a
                if not step:
                    log.warning('step: {step}为空')
                    continue
                if not isinstance(step, dict):
                    raise TypeError(f'步骤: {step}只支持字典格式')
                for key, value in step.items():
                    function = fixtures.get(key)
                    steps.append(dict(target=function, args=value))

    def do_pre_steps(self):
        log.debug(f'执行前置步骤: {self.pre_steps}')
        if not self.pre_steps:
            return []
        results = []
        for step in self.pre_steps:
            function = step.get('target')
            args = step.get('args')
            results.append(function(args))


    def do_post_steps(self):
        log.debug(f'执行后置步骤: {self.post_steps}')
        if not self.post_steps:
            return []
        results = []
        for step in self.post_steps:
            function = step.get('target')
            args = step.get('args')
            results.append(function(args))

    def parallel_run(self):
        times = self.times // self.concurrency
        results = []
        for i in range(times):
            log.info('执行步骤:', self.name, f'第{i+1}轮 并发量: {self.concurrency}' if self.times > 1 else '')

            threads = [MyThread(self.run) for i in range(self.concurrency)]
            [t.start() for t in threads]
            [t.join() for t in threads]
            results.extend([t.result for t in threads])

    def sequence_run(self):
        results = []
        for i in range(self.times):
            log.info('执行步骤:', self.name, f'第{i+1}轮' if self.times > 1 else '')
            result = self.run()
            results.append(result)
            self.context['result'] = self.result
        return results

    def should_skip(self):
        print('i run ---------')
        skip = self.skip
        print(skip)
        if isinstance(skip, str):
            try:
                skip = eval(skip)
            except Exception as ex:
                log.exception(ex)
                log.info('跳过步骤:', self.name, '原因: skip表达式出错')
                return True
        if skip:
            log.info('跳过步骤:', self.name, '原因: {self.skip}')
        print(skip)
        return skip

    def __call__(self, *args, **kwargs):
        if self.should_skip():
            return
        print(self.times, self.concurrency)
        run_function = self.parallel_run if self.concurrency else self.sequence_run
        try:
            pre_results = self.do_pre_steps()
            self.result = run_function()
            post_results = self.do_post_steps()
        except AssertionError as ex:
            log.exception(ex)
            self.status = 'FAIL'
        except Exception as ex:
            log.exception(ex)
            self.status = 'ERROR'
        else:
            self.status = 'PASS'
        return self.result

    @abstractmethod
    def run(self):
        pass

