import requests
from runnerz import Step


class Http(Step):
    def __init__(self, step, context):
        super().__init__(step, context)
        self.baseurl = self.config.get(BASEURL)
        context.setdefault(SESSION, requests.session())
        self.session = context.get(SESSION)

        request = self.config.get(REQUEST)
        if request:
            for key, value in request.items():
                self.session.__setattr__(key, value)

    def set_default_method(self, request):
        if request.get('data') or request.get('json') or request.get('files'):
            request.setdefault('method', 'post')
        else:
            request.setdefault('method', 'get')

    def pack_url(self, request):
        if not self.baseurl:
            return
        url = request.get('url')
        if not url.startswith('http'):
            request['url'] = '/'.join((self.baseurl.rstrip('/'), url.lstrip('/')))

    def send_request(self, request):
        # 发送请求
        print('   请求url:', request.get('url'))  # print(' 发送请求:', request)
        response = self.session.request(**request)  # 字典解包，发送接口
        print('   状态码:', response.status_code)  # print(' 响应数据:', response.text)

        try:
            res_dict = response.json()
        except Exception:
            res_dict = {}

        # 注册上下文变量
        step_result = dict(
            request=request,
            response=response,
            response_json=res_dict,
            status_code=response.status_code,
            response_text=response.text,
            response_headers=response.headers,
            response_time=response.elapsed.seconds,
            xpath=lambda expr: find_by_xpath(response.text, expr),
            jsonpath=lambda expr: find_by_jsonpath(response.text, expr),
            re=lambda expr: find_by_re(response.text, expr)
        )
        self.context['steps'].append(step_result)  # 保存步骤结果
        self.context.update(step_result)  # 将最近的响应结果更新到上下文变量中
        return response

    def process(self):
        request = self.step.get(REQUEST)
        request = self.parse(request)
        self.set_default_method(request)
        self.pack_url(request)
        return self.send_request(request)