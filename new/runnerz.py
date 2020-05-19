#
#
# class TestSuite(object):
#     def __init__(self):
#         self.name = None
#         self.description = None
#         self.config = None
#         self.variables = {}
#
#         self.test_cases = []
#         self.result = None
#         self.status = None
#
#
# class TestCase(object):
#     def __init__(self):
#         pass
#
#
# class TestStep(object):
#     def __init__(self):
#         pass
#
#
import unittest
#
# class TestA(unittest.TestCase):
#     @unittest.skip('hhh')
#     def test_a(self):
#         print('a')
#
#
# suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestA)
# for case in suite:
#     print(case.__dict__)
#
# result = unittest.TextTestRunner().run(suite)
# from pprint import pprint
# pprint(result.skipped[0][0].__dict__)


import ddt
from pprint import pprint

@ddt.ddt
class TestA(unittest.TestCase):
    @ddt.data(1,2,3)
    def test_a(self, value):
        pprint(self.__dict__)
        print(value)
        # for i in range(0, 6):
        #     with self.subTest(i=i):
        #         print(i)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestA)
result = unittest.TextTestRunner(verbosity=2).run(suite)