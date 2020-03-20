import logging
from selenium import webdriver

driver = webdriver.Chrome()


def open(url):
    driver.get(url)


def find(find_by):
    if not isinstance(find_by, str) or '=' not in find_by:
        raise TypeError(f'find_by: {find_by}参数应为包含"="的字符串')
    find_by = find_by.split('=')
    if find_by[0] not in ['id', 'name', 'class name', 'tag', 'link text', 'partical link text', 'css selector', 'xpath']:
        raise ValueError(f'定位方式不支持: {find_by[0]}')
    try:
        element = driver.find_element(*find_by)
    except Exception as ex:
        # logging.exception(ex)
        raise ex
    else:
        return element


def send_keys(find_by, text):
    element = find(find_by)
    element.clear()
    element.send_keys(text)


def click(find_by):
    element = find(find_by)
    element.click()
