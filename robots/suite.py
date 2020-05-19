import unittest
import types



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
                do_step(self.context, step)

        test_method.__name__ = f'test_{index+1}'
        test_method.__doc__ = attrs.get('Documentation')
        test_method.name = name
        test_method.tags = attrs.get('Tags')
        test_method.timeout = attrs.get('Timeout')
        return test_method


    def build(self, data: dict):
        context = variables = data.get('Variables')

        class TestRobot(unittest.TestCase):
            @classmethod
            def setUpClass(cls) -> None:
                cls.context = context

        keywords = data.get('Keywords')
        handle_keywords(keywords)

        tests = data.get('TestCases')
        [setattr(TestRobot, f'test_{index+1}', self.build_case(index, test)) for index, test in enumerate(tests)]

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRobot)
        return suite


    def run(self, suite):
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)