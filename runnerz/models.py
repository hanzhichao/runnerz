from runnerz.ensurez import ensure_type

BUILD_INS = {'name', 'extract', 'validate', 'skip', 'variables', 'config', 'tests', 'times', 'concurrency', 'steps'}
CASE_BUILD_INS = {'name', 'skip', 'variables', 'config', 'times', 'concurrency', 'steps', 'parameters'}


def split_and_strip(text, seq):
    return [item.strip() for item in text.split(seq)]


def _guess_steps(data: dict):
    ensure_type(data, dict)
    extra_keys = data.keys() - CASE_BUILD_INS
    if extra_keys:
        steps = [{key: data.get(key) for key in extra_keys}]
        return steps


class Keyword(object):
    """关键字/动作/插件抽象类"""
    def __init__(self, key: str, data: dict, parent=None):
        ensure_type(key, str)
        ensure_type(data, dict)
        self._key = key
        self._raw = data
        self._parent = parent
        self._docs = data.get('docs')
        self._args = data.get('args')
        self._skip = data.get('skip')
        self._steps = []
        self._return = data.get('return')

        self.build_steps()

    def build_steps(self):  # todo remove
        _steps = self._raw.get('steps') or _guess_steps(self._raw)
        if _steps:
            ensure_type(_steps, list)
            for _step in _steps:
                self._steps.append(Step(_step, parent=self))

    def __repr__(self):
        return f'<Keyword {self._key} {self._docs}>'


class Step(object):
    """步骤, 包含一个关键字"""
    def __init__(self, data: (str, dict), parent=None):
        self._raw = data
        self._parent = parent

        data = self._format_data(data)
        self._data = data
        self._name = data.get('name')
        self._skip = data.get('skip')
        self._times = data.get('times')  # todo ensure_type
        self._concurrency = data.get('concurrency')  # todo ensure_type

        self._target = None  # 目标函数
        self._kwargs = None # 目标函数参数

        self._extract = None
        self._validate = None

        self._guess_target()
        self.build_extract()
        self.build_validate()

    @staticmethod
    def _format_data(data: (str, dict))-> dict:
        ensure_type(data, (str, dict))
        if isinstance(data, dict):
            return data
        key = None
        func_name, *args = data.split()
        if '=' in func_name:
            key, func_name = split_and_strip(func_name, '=')

        _kwargs = {item.split('=', 1)[0]: item.split('=', 1)[1] for item in args if '=' in item}
        _args = [item for item in args if '=' not in item]

        if _args and _kwargs:
            _args.append(_kwargs)
            kwargs = _args
        else:
            kwargs = _kwargs or _args
        print('kwargs', kwargs)
        _data = {func_name: kwargs}
        if key:
            _data['extract'] = [{key: '$result'}]
        return _data

    def _guess_target(self):
        """猜测目标函数名"""
        extra_keys = self._data.keys() - BUILD_INS
        if extra_keys:
            self._target = extra_keys.pop()
            self._kwargs = self._data.get(self._target)

    def build_extract(self):
        self._extract = self._data.get('extract') or self._data.get('register')

    def build_validate(self):
        self._validate = self._data.get('validate') or self._data.get('check') or self._data.get('verify')

    def __repr__(self):
        return '<Step "%s" target: %s>' % (self._name, self._target)


class Case(object):
    """测试用例"""
    def __init__(self, data: dict, parent=None):
        ensure_type(data, dict)
        self._raw = data
        self._parent = parent
        self._name = data.get('name')
        self._skip = data.get('skip')
        self._tags = data.get('tags')
        self._level = data.get('level')
        self._parameters = data.get('parameters')
        self._steps = []

        self.build_steps()

    def build_steps(self):
        _steps = self._raw.get('steps') or _guess_steps(self._raw)
        if _steps:
            ensure_type(_steps, list)
            for _step in _steps:
                self._steps.append(Step(_step, parent=self))

    def __repr__(self):
        return '<Case "%s">' % self._name


class Suite(object):
    """测试套件, 对应一个文件"""  # todo 或目录
    def __init__(self, data: dict, path=None):
        ensure_type(data, dict)
        self._raw = data
        self._path = path
        self._name = data.get('name')
        self._config = self._raw.get('config')
        self._variables = self._raw.get('variables')
        self._cases = []
        self._keywords = []

        self.build_cases()
        self.build_keywords()

    def build_cases(self):
        _cases = self._raw.get('tests') or self._raw.get('testcases')
        if _cases:
            ensure_type(_cases, list)
            for _case in _cases:
                self._cases.append(Case(_case, parent=self))

    def build_keywords(self):
        _keywords = self._raw.get('keywords')
        if _keywords:
            ensure_type(_keywords, dict)
            for key, value in _keywords.items():
                self._keywords.append(Keyword(key, value, parent=self))

    def __repr__(self):
        return '<Suite "%s">' % self._name


if __name__ == '__main__':
    pass



