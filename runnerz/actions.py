# import requestz as requests
from operator import eq, gt, lt, ge, le
import re

import requests
from dubboz import Dubbo
from logz import log as logging
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from runnerz.utils.ensurez import ensure_type


def log(data: (str, list, dict), context):
    return logging.info(data)


def request(data: dict, context):
    ensure_type(data, dict)

    _session = context._variables.get('_session')
    base_url = context._variables.get('_base_url')
    if not _session:
        _session = requests.Session()
        context.register_variables({'_session': _session})

        _config = context._config
        if _config:
            ensure_type(_config, dict)
            _request_config = _config.get('request')
            if _request_config:
                ensure_type(_request_config, dict)
                if 'base_url' in _request_config:
                    base_url = _request_config.pop('base_url')
                    ensure_type(base_url, str)
                    context.register_variables({'_base_url': base_url})

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

    logging.info(res.text[:300])
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
    return result


def jsonschema(instance, schema):
    try:
        validate(instance, schema)
        return True
    except ValidationError as ex:
        raise AssertionError(ex)
        # return False


BUILD_IN_FUNCTIONS = {
    'request': request,
    'log': log,
    'dubbo': dubbo
}


COMPARE_FUNCS = dict(
    eq=eq, gt=gt, lt=lt, ge=ge, le=le,
    len_eq=lambda x, y: len(x) == len(y),
    str_eq=lambda x, y: str(x) == str(y),
    type_match=lambda x, y: isinstance(x, y),
    regex_match=lambda x, y: re.match(y, x),
    jsonschema=jsonschema
)