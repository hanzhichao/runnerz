# import requestz as requests
import requests
from dubboz import Dubbo
from logz import log as logging
from runnerz.utils.ensurez import ensure_type


def log(data: (str, list, dict), context):
    return logging.info(data)


def request(data: dict, context):
    ensure_type(data, dict)
    base_url = None
    headers = None

    _session = context._variables.get('_session')
    if not _session:
        _session = requests.Session()
        context.register_variables({'_session': _session})

    _config = context._config
    logging.debug('context', context)
    if _config:
        ensure_type(_config, dict)
        _request_config = _config.get('request')
        logging.debug('_request_config', _request_config ,'-'*20)
        if _request_config:
            ensure_type(_request_config, dict)
            if 'base_url' in _request_config:
                base_url = _request_config.pop('base_url')
                ensure_type(base_url, str)

            for key, value in _request_config.items():
                try:
                    setattr(_session, key, value)  # todo 异常处理
                except:
                    logging.warning(f'Session会话不支持设置属性: {key}={value}')

    url = data.get('url', '')
    ensure_type(url, str)
    if base_url and not url.startswith('http'):
        data['url'] = '/'.join((base_url.rstrip('/'), url.lstrip('/')))

    res = _session.request(**data)

    context.register_variables(
        {
            'content': res.json(),  # todo
            'status_code': res.status_code
        }
    )

    logging.debug(res.text)
    return res


def dubbo(data: dict, context):
    ensure_type(data, dict)
    host = data.get('host')
    port = data.get('port')
    service = data.get('service')
    method = data.get('method')
    params = data.get('params')
    client = Dubbo(host=host, port=port)
    result = client.invoke(service, method, params)
