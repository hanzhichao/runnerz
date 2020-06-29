import re
import json

from jsonpath import jsonpath
from lxml import etree
from lxml.etree import HTMLParser
from logz import log


def find_by_jsonpath(text, expr):
    try:
        res_dict = json.loads(text)
    except Exception as ex:
        log.exception(ex)
        return
    result = jsonpath(res_dict, expr)
    if result and len(result) == 1:
        return result[0]
    return result


def find_by_re(text, expr):
    result = re.findall(expr, text)
    if result and len(result) == 1:
        return result[0]
    return result


def find_by_xpath(text, expr):
    try:
        html = etree.HTML(text, etree.HTMLParser())
        result = html.xpath('expr')
    except Exception:
        result = False
    if result and len(result) == 1:
        return result[0]
    return result