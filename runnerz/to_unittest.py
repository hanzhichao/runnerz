import os
import unittest

from filez import file

from runnerz.step import StepGroup, Step
from runnerz.function import request

BASEDIR = os.path.dirname(os.path.dirname(__file__))
DATADIR = os.path.join(BASEDIR, 'data')

data_file = os.path.join(DATADIR, 'data.yml')
data = file.load(data_file)

TestTemplete = type('TestTemplate',
                    (unittest.TestCase,),
                    {'__doc__': data.get('name')})
context = {}
context['functions'] = {'request': request}

step_group = StepGroup(data)

for index, step in enumerate(step_group.sub_steps):
    case = lambda self: StepGroup(step, context)()
    setattr(TestTemplete, f'test_method_{index+1}', case)


if __name__ == '__main__':
    unittest.main(verbosity=2)