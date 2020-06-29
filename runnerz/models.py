import os
from abc import ABCMeta, abstractmethod

from runnerz.utils.ensurez import ensure_type

BUILD_INS = {'name', 'extract', 'validate', 'skip', 'variables', 'config', 'tests', 'times', 'concurrency'}

# class Config(object):
#     """配置对象, 适用于Suite"""  # todo 适用于Case
#     def __init__(self, data: dict):
#         ensure_type(data, dict)
#         self._raw = data
#         self._variables = None
#
#         self.build_variables()
#
#     def build_variables(self):
#         _variables = self._raw.get('variables')
#         ensure_type(_variables, dict)
#         self._variables = _variables
#
#     def __repr__(self):
#         return '<Config variables: %s>' % self._variables


class Keyword(object):
    """关键字/动作/插件抽象类"""
    def __init__(self, target, kwargs):
        ensure_type(target, str)
        ensure_type(kwargs, dict)
        self._target = target
        self._kwargs = kwargs


class Step(object):
    """步骤, 包含一个关键字"""
    def __init__(self, data: dict):
        ensure_type(data, dict)
        self._raw = data
        self._name = data.get('name')
        self._skip = data.get('skip')
        self._target = None  # 目标函数
        self._kwargs = None # 目标函数参数

        self._extract = None
        self._validate = None

        self._guess_target()
        self.build_extract()
        self.build_validate()

    def _guess_target(self):
        """猜测目标函数名"""
        extra_keys = self._raw.keys() - BUILD_INS
        if extra_keys:
            self._target = extra_keys.pop()
            self._kwargs = self._raw.get(self._target)

    def build_extract(self):
        self._extract = self._raw.get('extract') or self._raw.get('register')

    def build_validate(self):
        self._validate = self._raw.get('validate') or self._raw.get('check') or self._raw.get('verify')

    def __repr__(self):
        return '<Step "%s">' % self._name

class Case(object):
    """测试用例"""
    def __init__(self, data):
        ensure_type(data, dict)
        self._raw = data
        self._name = data.get('name')
        self._skip = data.get('skip')
        self._steps = []

        self.build_steps()

    def build_steps(self):
        _steps = self._raw.get('steps')
        if _steps:
            ensure_type(_steps, list)
            for _step in _steps:
                self._steps.append(Step(_step))

    def __repr__(self):
        return '<Case "%s">' % self._name


class Suite(object):
    """测试套件, 对应一个文件"""  # todo 或目录
    def __init__(self, data: dict):
        ensure_type(data, dict)
        self._raw = data
        self._name = data.get('name')
        self._cases = []
        self._config = None
        self._context = None

        self.build_config()
        self.build_cases()

    def build_config(self):
        """解析config"""
        _config = self._raw.get('config')
        if _config:
            ensure_type(_config, dict)
            self._config = _config

    def build_cases(self):
        _cases = self._raw.get('tests') or self._raw.get('testcases')
        if _cases:
            ensure_type(_cases, list)
            for _case in _cases:
                self._cases.append(Case(_case))

    def __repr__(self):
        return '<Suite "%s">' % self._name


if __name__ == '__main__':
    pass



