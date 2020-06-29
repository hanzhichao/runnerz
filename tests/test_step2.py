
from runnerz.base import Step
from robots.utils import parse_dollar

def test_format_data():
    s = Step('b=log hello,$a')
    print(s.data)
    assert s.target == 'log'
    assert s.key == 'b'
    assert 'hello,$a' in s.args

def test_dict_data():
    data = {'name': '步骤1', 'target': 'get', 'args': ['https://www.baidu.com'], 'kwargs': {'params': {'a': 1, 'b':2}}}
    s = Step(data)
    print(s.data)
    assert s.name == '步骤1'
    assert s.target == 'get'

def test_util_parse():
    context = {'a': 1}
    assert parse_dollar(context, 'hello,$a') == 'hello,1'

def test_parse():
    s = Step('b=log hello,$a')
    context = {
        'variables': {'a': 100}
    }
    print(s.data)
    s.parse(context)
    print('s.tests', s.data)
    assert s.target == 'log'
    assert s.key == 'b'
    assert 'hello,100' in s.args