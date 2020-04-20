import random

from runnerz.keywords import *
from runnerz.base import Base
from runnerz.utils import get_section, is_step, get_function


class StepGroup(Base):  # testcase   steps
    def __init__(self, data, context=None):
        super().__init__(data, context)
        self.run_mode = data.get(RUN_MODE)
        self.sub_steps = get_section(data, SUB_STEPS)

    def run(self, data, context):
        self.result = []
        for step in self.sub_steps:
            if is_step(step):
                self.result.append(Step(step, context)())
            else:
                self.result.extend(StepGroup(step, self.context)())
        return self.result


class Step(Base):
    def __init__(self, data, context=None):
        super().__init__(data, context)

    def run(self, data, context):
        action = get_function(self.data, self.context)
        if action and callable(action):
            return action(self.data, self.context)


if __name__ == '__main__':
    import yaml
    with open('/Users/apple/Documents/Projects/Self/PyPi/data/data.yml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    context = {}
    from runnerz.function import request
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
