from tmp.utils import merge_update


def test_merge_update():
    d1 = dict(baseurl='http://www.baidu.com', request={'headers': {"x-text": 1},'verfiy': False}, a=1)
    d2 = dict(baseurl='http://www.hao123.com', request={'headers': {"x-text1": 1},'timeout': 3}, b=3)
    merge_update(d1, d2)
    print(d1)
