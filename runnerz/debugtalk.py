def add(a,b):
    return a+b

def setup(request):
    print('setup')
    print(request)

def teardown(response):
    print('teardown')
    # print(response.resp_obj.text)  # 原始请求文本