# from string import Template
# import re
# def add(a, b):
#     return a+b
#
# a = 1
# b = 2
#
# s = '$a, $b, ${add($a, $b)}'
#
# s1 = Template(s).safe_substitute(dict(a=a,b=b,add=add))
#
# print(s1)
#
#
# result = re.findall(r'\$\{(?P<func>.*?)\}', s1)
# print(result)
# for expr in result:
#     print(eval(expr, {}, dict(add=add)))
#
# def t(m):
#     if not m:
#         return m
#
#     print(m.group(1))
#     return str(eval(m.group(1)))
#
# s2 = re.sub(r'\$\{(.*?)\}', t, s1)
# print(s2)
#
# print(dir(1))
#
# # 1. 实现步骤解析
# import unittest
#
# tests = [1,2,3,4,5]
#
# class TestsDemo(unittest.TestCase):
#     def test_a(self):
#         for item in tests:
#             with self.subTest(item=item):
#                 self.assertGreater(item, 2)
#
# if __name__ == '__main__':
# #     unittest.main()
# import re
# context = {'a': 1, 'b': 2, 'except': 3}
# text = '$a + $b = $except'
#
# def repl_func(matched):
#     if matched:
#         text = matched.group(1)
#         return str(context.get(text))
#
# result = re.sub('\$(\w+)', repl_func, text)
# print(result)

# import jinja2
#
# def add(x):
#     return x+3
#
# # env = jinja2.Environment()
# # env.filters['add'] = add
#
# text = '''
# {{ a| add}}
# '''
# t = jinja2.Template(text)
# print(t)
# #
# r=jinja2.Template(text).render(dict(a=3))
# print(r)
import re
text = '${P(tests.csv)}'
CSV_REGEXT = re.compile('\${P\((?P<csv>.*?)\)}')
r = re.match(CSV_REGEXT, text)
print(r.group(1))