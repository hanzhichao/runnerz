from abc import ABCMeta, abstractmethod
from logz import log

from runnerz.keywords import *


class Base(object, metaclass=ABCMeta):  # 节点通用
    def __init__(self, data, context=None):
        self.data = data

        self.name = data.get(NAME)
        self.description = data.get(DESCRIPTION)
        self.tags = data.get(TAGS)
        self.level = data.get(LEVEL)

        self.config = data.get(CONFIG)
        self.variables = data.get(VAIABLES, {})  # 在项目中还是config中?

        self.skip = data.get(SKIP)
        self.timeout = data.get(TIMEOUT)
        self.times = data.get(TIMES)  # 3 or rerun  (3, 1, 'on_fail/on_error/always')
        self.concurrency = data.get(CONCURRENCY)

        self.result = None
        self.status = None

        self.context = context or {}
        self.context.setdefault(CONFIG, {})
        self.context.setdefault(VAIABLES, {})
        if self.config:
            self.context[CONFIG].update(self.config)
            config_variables = self.config.get(VAIABLES)
            if config_variables:
                self.variables.update(config_variables)
        if self.variables:
            self.context[VAIABLES].update(self.variables)


    def __call__(self, *args, **kwargs):
        try:
            self.result = self.run()
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

