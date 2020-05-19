import unittest

class TestsContainer(unittest.TestCase):
    longMessage = True

    testsmap = {
        'foo': [1, 1],
        'bar': [1, 2],
        'baz': [5, 5],
        'baf': [5, 6],
    }

    def test_a(self):
        for name, (a, b) in self.testsmap.items():
            with self.subTest(name=name):
                self.assertEqual(a, b, name)

if __name__ == '__main__':
    result = unittest.main()
    print(result)