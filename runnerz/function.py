import requests
from logz import log, logit

from runnerz.keywords import NAME, CHECK, EXTRACT, VAIABLES, CONFIG, REQUEST_SESSION, REQUEST
from runnerz.decorator import step


def set_default_method(request):
    if request.get('tests') or request.get('json') or request.get('files'):
        request.setdefault('method', 'post')
    else:
        request.setdefault('method', 'get')


def pack_url(config, request: dict):
    if not isinstance(request, dict):
        raise TypeError(f'request: {request} 必须为字典格式')
    log.warning('pack url', request, 'config', config)
    request_config = config.get('request', {})  # todo keywords
    baseurl = request_config.get('base_url') or request_config.get('baseurl') or config.get('base_url') or config.get('baseurl') # todo
    if not baseurl:
        return
    url = request.get('url')
    if not url.startswith('http'):
        request['url'] = '/'.join((baseurl.rstrip('/'), url.lstrip('/')))


def set_default_request(config, session):
    request = config.get(REQUEST)
    if request:
        for key, value in request.items():
            session.__setattr__(key, value)


@step
def request(data, context):
    log.info('执行请求步骤: ', data.get(NAME))
    req = data.get(REQUEST)
    variables = context.get(VAIABLES)  # todo 改为result
    config = context.get(CONFIG)
    context.setdefault(REQUEST_SESSION, requests.session())
    session = context.get(REQUEST_SESSION)
    if config and isinstance(config, dict):
        # 组装url
        pack_url(config, req)
        # 设置默认请求想
        set_default_request(config, session)

    # 设置默认方法
    set_default_method(req)

    if req and isinstance(req, dict):
        res = session.request(**req)
        # 注册变量
        variables['response'] = res
        variables['response_json'] = res.json()  # todo
        variables['content'] = res.json()  # todo
        variables['status_code'] = res.status_code

        log.debug('请求数据:', req, '响应数据:', res.text)
        return res