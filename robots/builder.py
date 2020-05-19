import unittest
import types


from logz import logit
from robots.utils import parse_dollar, split_and_strip


class Step(object):
    def __init__(self):
        pass


class StepBuilder(object):
    """解析并生成Step"""
    def _parse_args(self, context: dict, *args):
        return [parse_dollar(context, arg) for arg in args]

    def _parse_kwargs(self, context: dict, **kwargs):
        return {parse_dollar(context, key): parse_dollar(context, value) for key, value in kwargs.items()}

    def _do_step(self, context, expr):
        if isinstance(expr, str):
            func_name, *args = expr.split()
            print('args', args)
            key = None
            if '=' in func_name:
                key, func_name = split_and_strip(func_name, '=')

            kwargs = {item.split('=', 1)[0]: item.split('=', 1)[1] for item in args if '=' in item}
            args = [item for item in args if '=' not in item]
            args = self._parse_args(context, *args)
            kwargs = self._parse_kwargs(context, **kwargs)
            func = functions.get(func_name)
            if func:
                result = func(*args, **kwargs)
                context['result'] = context['$'] = result

                if key:
                    context[key] = result
                return result


    def run(self, context, expr: (str, dict)):
        filters = None
        # if isinstance(expr, dict):
        #     key, expr = tuple(expr.items())[0]  # fixme

        result = self._do_step(context, expr)



class KeywordBuilder(object):
    def build_keyword(self, name: str, attrs: dict) -> dict:
        doc = attrs.get('Documention')
        arg_names = attrs.get('Arguments', [])
        steps = attrs.get('Steps', [])
        func_return = attrs.get('Return')

        def func(*args):
            kwargs = dict(zip(arg_names, args))
            locals().update(kwargs)
            for step in steps:
                step.run(locals(), step)
            return locals().get(func_return)

        func.__name__ = name
        func.__doc__ = doc
        return {name: func}

    def build_keywords(self, keywords: dict) -> list:
        return [self.build_keyword(name, attrs) for name, attrs in keywords.items()]


class TestSuiteBuilder(object):
    def build_case(self, index:int, test: dict) -> types.FunctionType:
        name, attrs = tuple(test.items())[0]
        def test_method(self):
            if attrs.get('Skip'):
                raise unittest.SkipTest('Skip=True跳过用例')
            if attrs.get('Variables'):
                self.context.update(attrs.get('Variables'))
            steps = attrs.get('Steps')
            for step in steps:
                step.run(self.context, step)

        test_method.__name__ = f'test_{index+1}'
        test_method.__doc__ = attrs.get('Documentation')
        test_method.name = name
        test_method.tags = attrs.get('Tags')
        test_method.timeout = attrs.get('Timeout')
        return test_method


    def build_suite(self, data: dict):
        context = variables = data.get('Variables')

        class TestRobot(unittest.TestCase):
            @classmethod
            def setUpClass(cls) -> None:
                cls.context = context

        keywords = data.get('Keywords')
        new_function_list = KeywordBuilder().build_keywords(keywords)  # todo update

        tests = data.get('TestCases')
        [setattr(TestRobot, f'test_{index+1}', self.build_case(index, test)) for index, test in enumerate(tests)]

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRobot)
        return suite
