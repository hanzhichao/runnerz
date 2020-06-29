import requests
from logz import log as logging
from runnerz.utils.ensurez import ensure_type


def log(data: (str, list, dict), context):
    return logging.info(data)


def request(data: dict, context):
    ensure_type(data, dict)

    base_url = None
    headers = None
    _config = context._config
    logging.debug('context', context)
    if _config:
        ensure_type(_config, dict)
        _request_config = _config.get('request')
        logging.debug('_request_config', _request_config ,'-'*20)
        if _request_config:
            ensure_type(_request_config, dict)
            base_url = _request_config.get('base_url')
            ensure_type(base_url, str)
            headers = _request_config.get('headers')
            ensure_type(headers, dict)

    url = data.get('url', '')
    ensure_type(url, str)
    if base_url and not url.startswith('http'):
        data['url'] = '/'.join((base_url.rstrip('/'), url.lstrip('/')))

    # todo register session
    res = requests.request(**data)

    context.register_variables(
        {
            'content': res.json(),  # todo
            'status_code': res.status_code
        }
    )

    logging.debug(res.text)
    return res

