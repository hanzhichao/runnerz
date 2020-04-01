import requests

from runnerz.keywords import NAME, CHECK, EXTRACT, VAIABLES
from runnerz.decorator import step

@step
def request(data, context=None):
    print('执行请求步骤: ', data.get(NAME))
    req = data.get('request')
    variables = context.get(VAIABLES)  # todo 改为result

    if req and isinstance(req, dict):
        res = requests.request(**req)
        variables['response'] = res
        variables['response_json'] = res.json()
        variables['status_code'] = res.status_code

        print('请求数据:', req, '状态码:', res.status_code)
        return res