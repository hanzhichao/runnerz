import os
from string import Template
from collections import ChainMap

import yaml
import requests

# 步骤定义
CONFIG = 'config'  # 配置关键字  settings
TESTS = 'tests'
STEPS = 'steps'  # 步骤关键字  steps/teststeps/testcases

NAME = 'name'  # 名称
VARIABLES = 'variables'  # 用户自定义变量关键字
BASE_URL = 'base_url'
REQUEST = 'request'  # 请求配置,请求数据关键字
CHECK = 'verify'  # 验证关键字  check/validate/assert
EXTRACT = 'extract'   # 提取关键字 output/register
SKIP = 'skip'  # 跳过步骤关键字
TIMES = 'times'  # 循环步骤关键字  circle


def run(data):
    # 初始化
    session = requests.session()
    context = ChainMap({}, os.environ)
    base_url = ''

    suite_name = data.get(NAME, '')
    print('执行测试套件:', suite_name)

    # 使用环境变量预解析
    data_str = yaml.dump(data, default_flow_style=False)  # 先转为字符串
    if '$' in data_str:
        data_str = Template(data_str).safe_substitute(context)  # 替换${变量}为varables中的同名变量
        data = yaml.safe_load(data_str)  # 重新转为字典

    # 解析配置
    config = data.get(CONFIG)
    if config:
        variables = config.get(VARIABLES, {})
        if variables:
            context.update(variables)
        base_url = config.get(BASE_URL)
        request = config.get(REQUEST)
        if request:
            for key, value in request.items():
                session.__setattr__(key, value)

    # 解析用例
    tests = data.get(TESTS, [])
    context['tests'] = []
    for case_index, case in enumerate(tests):
        case_name = case.get(NAME, '')
        print(' 执行用例:', case_name)

        # 解析步骤
        context['tests'].append([])  # 用于保存所有步骤的请求和响应, 便于跨步骤引用

        steps = case.get(STEPS, [])
        for step in steps:
            step_name = step.get(NAME)
            skip = step.get(SKIP)
            times = step.get(TIMES, 1)
            request = step.get(REQUEST)
            if skip or not request:
                print(' 跳过步骤:', step_name)
                continue

            for i in range(times):
                print(' 执行步骤:', step_name, f'第{i+1}轮' if step.get(TIMES) else '')
                # 请求$变量解析
                if not request:
                    continue
                request_str = yaml.dump(request, default_flow_style=False)  # 先转为字符串
                if '$' in request_str:
                    request_str = Template(request_str).safe_substitute(context)  # 替换${变量}为varables中的同名变量
                    request = yaml.safe_load(request_str)  # 重新转为字典
                # 设置默认请求方法
                if request.get('data') or request.get('json') or request.get('files'):
                    request.setdefault('method', 'post')
                else:
                    request.setdefault('method', 'get')
                # 组装baseurl
                if base_url:
                    url = request.get('url')
                    if not url.startswith('http'):
                        request['url'] = '/'.join((base_url.rstrip('/'), url.lstrip('/')))

                # 发送请求
                print('  请求url:', request.get('url'))  # print(' 发送请求:', request)
                response = session.request(**request)  # 字典解包，发送接口
                print('  状态码:', response.status_code)  # print(' 响应数据:', response.text)

                # 注册上下文变量
                step_result = dict(
                    request=request,
                    response=response,
                    status_code=response.status_code,
                    response_text=response.text,
                    response_headers=response.headers,
                    response_time=response.elapsed.seconds
                )
                context['tests'][case_index].append(step_result)  # 保存步骤结果
                context.update(step_result)  # 将最近的响应结果更新到上下文变量中

                # 提取变量
                extract = step.get(EXTRACT)
                if extract is not None:  # 如果存在extract
                    for key, value in extract.items():
                        print("  提取变量:", key, value)
                        # 计算value表达式，可使用的全局变量为空，可使用的局部变量为RESPONSE(响应对象)
                        context[key] = eval(value, {}, context)  # 保存变量结果到上下文中
                # 处理断言
                check = step.get(CHECK)
                if check and isinstance(check, list):
                    for line in check:
                        result = eval(line, {}, context)  # 计算断言表达式，True代表成功，False代表失败
                        print("  处理断言:", line, "结果:", "PASS" if result else "FAIL")
    return context['tests']


if __name__ == "__main__":
    with open('/Users/apple/Documents/Projects/runnerz/data.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    result = run(data)
    print(result)