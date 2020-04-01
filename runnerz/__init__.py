# import os
# from string import Template
# from collections import ChainMap
#
# import random
# import json
# import operator
#
# from jsonschema import validate
#
# from logz import log
#
# from runnerz.keywords import *
# from runnerz.plugins.http import Http
# from runnerz.thread import MyThread
#
# log.format = '%(asctime)s %(threadName)s %(levelname)s %(message)s'
# print = log.info
#
# BASEDIR = os.path.dirname(os.path.dirname(__file__))
# SCHEMA_FILE = os.path.join(BASEDIR, 'schema.json')
#
#
# class Base(object):  # 节点通用
#     def __init__(self, data):
#         self.name = data.get(NAME)
#         self.description = data.get(DESCRIPTION)
#         self.tags = data.get(TAGS)
#         self.level = data.get(LEVEL)
#
#         self.config = data.get(CONFIG)
#         self.skip = data.get(SKIP)
#         self.timeout = data.get(TIMEOUT)
#         self.times = data.get(TIMES)  # 3 or rerun  (3, 1, 'on_fail/on_error/always')
#         self.concurrency = data.get(CONCURRENCY)
#
#
#         self.result = None
#         self.status = None
#
#     def _run(self):
#         pass
#
#     def _post(self):
#         pass
#
#     def process(self):
#         pass
#
#     def run(self):
#         try:
#             self.result = self._run()
#         except AssertionError as ex:
#             # log.exception(ex)
#             self.status = 'FAIL'
#             raise ex
#         except Exception as ex:
#             # log.exception(ex)
#             self.status = 'ERROR'
#             raise ex
#         else:
#             self.status = 'PASS'
#         return self.result
#
#
# class Step(Base):
#     def __init__(self, step, context):
#         super().__init__(step, context)
#         self.step = self.data
#
#         self.times = step.get(TIMES, 1)
#         self.run_type = step.get(RUN_TYPE)
#         self.check = step.get(CHECK)
#         self.extract = step.get(EXTRACT)
#         self.concurrency = step.get(CONCURRENCY, 1)
#
#     def parse(self, data):
#         data_str = yaml.dump(data, default_flow_style=False)  # 先转为字符串
#         if '$' in data_str:
#             data_str = Template(data_str).safe_substitute(self.context)  # 替换${变量}为varables中的同名变量
#             data = yaml.safe_load(data_str)  # 重新转为字典
#         return data
#
#     def post_check(self):
#         # 处理断言
#         results = []
#         for line in self.check:
#             if isinstance(line, str):
#                 result = eval(line, {}, self.context)  # 计算断言表达式，True代表成功，False代表失败
#             elif isinstance(line, dict):
#                 for key, value in line.items():
#                     if hasattr(operator, key):
#                         func = getattr(operator, key)
#                         items = []
#                         for item in value:
#                             if isinstance(item, str):
#                                 item = self.context.get(item, item)
#                             items.append(item)
#
#                         result = func(*items)
#             print("   处理断言:", line, "结果:", "PASS" if result else "FAIL")
#             results.append(result)
#         if not all(results):
#             raise AssertionError('断言失败')
#
#     def post_extract(self):
#         for key, value in self.extract.items():
#             # 计算value表达式，可使用的全局变量为空，可使用的局部变量为RESPONSE(响应对象)
#             result = eval(value, {}, self.context)  # 保存变量结果到上下文中
#             print("   提取变量:", key, value, "结果:", result)
#             self.context[key] = result
#
#     def parallel_run(self):
#         times = self.times // self.concurrency
#         results = []
#         for i in range(times):
#             print('  执行步骤:', self.name, f'第{i+1}轮 并发量: {self.concurrency}' if self.times > 1 else '')
#
#             threads = [MyThread(self.process) for i in range(self.concurrency)]
#             [t.start() for t in threads]
#             [t.join() for t in threads]
#             results.extend([t.result for t in threads])
#
#     def sequence_run(self):
#         results = []
#         for i in range(self.times):
#             print('  执行步骤:', self.name, f'第{i+1}轮' if self.times > 1 else '')
#             result = self.process()
#             results.append(result)
#             self.context['result'] = self.result
#         return results
#
#     def _run(self):
#         if self.skip:
#             print('  跳过步骤:', self.name)
#             return
#         if self.concurrency > 1:
#             result = self.parallel_run()
#         else:
#             result = self.sequence_run()
#
#
#         if self.check:
#             self.post_check()
#
#         if self.extract:
#             self.post_extract()
#         return result
#
#     def process(self):
#         pass
#
#
# class Stage(Base):  # steps
#     def __init__(self, stage, context):
#         super().__init__(data, context)
#         self.stage = stage
#         self.run_type = stage.get(RUN_TYPE)
#         self.steps = stage.get(STEPS)
#         self.context['steps'] = []
#
#     def parallel_run(self):
#         threads = []
#         results = []
#         for step in self.steps:
#             action = Http(step, self.context)
#             threads.append(MyThread(action.run))
#         [t.start() for t in threads]
#         [t.join() for t in threads]
#         results.extend([t.result for t in threads])
#         return results
#
#     def sequence_run(self):
#         results = []
#         for step in self.steps:
#             result = Http(step, self.context).run()
#             results.append(result)
#         return results
#
#     def _run(self):
#         print(' 执行stage:', self.name, '运行方式:', self.run_type)
#         if self.run_type == 'parallel':
#             return self.parallel_run()
#         elif self.run_type == 'random':
#             random.shuffle(self.steps)
#         return self.sequence_run()
#
#
# class Flow(Base):
#     def __init__(self, data, context={}):
#         super().__init__(data, context)
#         self.config = data.get(CONFIG, {})
#
#         self.variables = self.config.get(VAIABLES, {})
#         self.context = ChainMap(self.variables, os.environ)
#         self.context[CONFIG] = self.config
#         self._validate()
#
#     def _validate(self):
#         with open(SCHEMA_FILE) as f:
#             schema = json.load(f)
#
#         validate(instance=self.data, schema=schema)
#
#     def _run(self):
#         print('执行流程:', self.name)
#         stages = data.get(STAGES)
#         results = []
#         for stage in stages:
#             result = Stage(stage, self.context).run()
#             results.append(result)
#         return results
#
#     def run(self):
#         try:
#             self.result = self._run()
#         except AssertionError as ex:
#             log.exception(ex)
#             self.status = 'FAIL'
#         except Exception as ex:
#             log.exception(ex)
#             self.status = 'ERROR'
#         else:
#             self.status = 'PASS'
#         return self.result
#
#
# if __name__ == "__main__":
#     import yaml
#     with open('/Users/apple/Documents/Projects/Self/PyPi/runnerz/data.yml', encoding='utf-8') as f:
#         data = yaml.safe_load(f)
#
#     f = Flow(data)
#     print(f.run())
#     print(f.status)
#     print(f.result)
