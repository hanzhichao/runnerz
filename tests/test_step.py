import os

import yaml
from filez import file
from runnerz.step import StepGroup

from runnerz.function import request

BASEDIR = os.path.dirname(os.path.dirname(__file__))
DATADIR = os.path.join(BASEDIR, 'data')


def test_step_group_with_data():
    data_file = os.path.join(DATADIR, 'data.yml')
    data = file.load(data_file)
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
    data_file = os.path.join(DATADIR, 'data.yml')
    data = file.load(data_file)
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    g()

def test_with_data():
    data_file = os.path.join(DATADIR, 'data2.yaml')
    data = file.load(data_file)
    context = {}
    context['functions'] = {'request': request}
    g = StepGroup(data, context)
    g()