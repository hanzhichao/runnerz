import random

from runnerz.keywords import *
from runnerz.base import Base
from runnerz.utils import get_section, is_step, get_function
from runnerz.thread import MyThread
# from runnerz.plugins.http import Http
from runnerz.function import request


class StepGroup(Base):  # steps
    def __init__(self, data, context=None):
        super().__init__(data, context)
        self.run_mode = data.get(RUN_MODE)
        self.sub_steps = get_section(data, SUB_STEPS)

    def run(self):
        self.result = []
        for step in self.sub_steps:
            if is_step(step):
                self.result.append(Step(step, self.context).run())
            else:
                self.result.extend(StepGroup(step, self.context).run())
        return self.result


class Step(Base):
    def __init__(self, data, context=None):
        super().__init__(data, context)

    def run(self):
        print()
        action = get_function(self.data, self.context)
        if action and callable(action):
            return action(self.data, self.context)


if __name__ == '__main__':
    import yaml
    with open('/Users/apple/Documents/Projects/Self/PyPi/runnerz/data.yml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    # print(g.name)
    # print(g.config)
    # print(g.sub_steps)
    # print(g.context)
    # from runnerz.function import request
    # from runnerz.decorator import functions
    #
    # print(functions)
    # print(g.context)
    g.run()
