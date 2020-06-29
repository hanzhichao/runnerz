import os
from filez import file

BASEDIR = os.path.dirname(os.path.dirname(__file__))

data1 = file.load(os.path.join(BASEDIR, 'tests', 'data', 'runnerz_01.yaml'))
from runnerz import models
from runnerz.runner import Runner, UnittestRunner



def test_models():
    suite = models.Suite(data1)
    print(suite)
    print(suite._config)
    print(suite._cases)
    print(suite._cases[0]._steps)
    print(suite._cases[0]._steps[0]._target)
    print(suite._cases[0]._steps[0]._extract)
    print(suite._cases[0]._steps[0]._validate)


def test_runner():
    suite = models.Suite(data1)
    case = suite._cases[0]
    step = case._steps[0]
    runner = Runner()
    runner.run_suite(suite)


def test_unittest_runner():
    suite = models.Suite(data1)
    case = suite._cases[0]
    step = case._steps[0]
    runner = UnittestRunner()
    runner.run(suite)