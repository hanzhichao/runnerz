import yaml
import requests
from string import Template

with open('data.yaml', encoding='utf-8') as f:
    apis = yaml.safe_load(f)

for api in apis:
    print("处理请求:", api.get('name'))
    request = api.get('request', {})  # 请求报文，默认值为{}
    # 处理参数化请求中的${变量}
    request_str = yaml.dump(request)  # 先转为字符串
    if '$' in request_str:
        request_str = Template(request_str).safe_substitute(locals())  # 替换${变量}为局部变量中的同名变量
        request = yaml.safe_load(request_str)  # 重新转为字典
    # 发送请求
    res = requests.request(**request)  # 字典解包，发送接口
    # 提取变量
    extract = api.get('extract')
    if extract is not None:  # 如果存在extract
        for key, value in extract.items():
            # 计算value表达式，可使用的全局变量为空，可使用的局部变量为RESPONSE(响应对象)
            # 保存变量结果到局部变量中
            print("提取变量:", key, value)
            locals()[key] = eval(value, {}, {'RESPONSE': res})
    # 处理断言
    verify = api.get('verify')
    if verify is not None:
        for line in verify:
            result = eval(line, {}, {'RESPONSE': res}) # 计算断言表达式，True代表成功，False代表失败
            print("断言:", line, "结果:", "PASS" if result else "FAIL")
