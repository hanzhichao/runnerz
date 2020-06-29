import os

from filez import file
from runnerz.base import StepGroup

from runnerz.function import request

BASEDIR = os.path.dirname(os.path.dirname(__file__))
DATADIR = os.path.join(BASEDIR, 'tests', 'data')


def test_step_group_with_data():
    data = file.load(os.path.join(DATADIR, 'runnerz_01.yaml'))
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    g()


def test_step_group_with_testsuite():
    data_file = os.path.join(DATADIR, 'testsuite.json')
    data = file.load(data_file)
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    g()


def test_step_with_fixtues():
    data_file = os.path.join(DATADIR, 'tests.yml')
    data = file.load(data_file)
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    g()


def test_with_data():
    data_file = os.path.join(DATADIR, 'httprunner_01.yaml')
    data = file.load(data_file)
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    g()