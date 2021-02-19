import datetime
import os
import time
import traceback
from random import random

from selenium import webdriver
import signal
from contextlib import contextmanager

cnt = 0


def wait_until(start_time):
    # start_time = datetime.datetime(2020, 7, 2, 6, 50)
    seconds_until_release_time = (start_time - datetime.datetime.now()).total_seconds()
    if seconds_until_release_time > 0:
        time.sleep(seconds_until_release_time)


def log(string):
    print("[{}] {}".format(datetime.datetime.now(), string))


def log_exception(e, driver, site):
    print("[{}] Exception: {}\n    Exception Msg: {}".format(datetime.datetime.now(), type(e), e))
    save_page(driver, site)


def type_with_delay(driver, xpath, value):
    try:
        if driver.find_elements_by_xpath(xpath):
            driver.find_elements_by_xpath(xpath)[0].clear()
            for c in value:
                driver.find_elements_by_xpath(xpath)[0].send_keys(c)
                time.sleep(random() / 10)
        else:
            log("xpath not found: {}".format(xpath))
            return False
    except Exception:
        traceback.print_exc()
        return False
    return True


def reset_browser(driver):
    driver.quit()
    driver = webdriver.Chrome('/usr/local/bin/chromedriver')
    return driver


def save_page(driver, site):
    try:
        content = driver.page_source
        file_name = str(counter())
        file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log",
                                datetime.datetime.today().strftime('%Y-%m-%d'), site)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        html_file_path = os.path.join(file_dir, file_name + '.html')
        log("Saving {}".format(html_file_path))
        with open(html_file_path, 'w+') as f:
            f.write(content)
        screenshot_file_path = os.path.join(file_dir, file_name + '.png')
        driver.get_screenshot_as_file(screenshot_file_path)
    except Exception as e:
        print("save_page Exception:{}".format(e))


def counter():
    global cnt
    cnt += 1
    return cnt


class TimeLimitException(Exception): pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        print("Timed limit exceeded. Frame: {}".format(frame))
        raise TimeLimitException

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
#
# a = webdriver.Chrome('/usr/local/bin/chromedriver')
#
# d = webdriver.Chrome('/usr/local/bin/chromedriver')
# a.get("https://www.nike.com/launch")
# d.get("https://www.nike.com/launch")
# time.sleep(20)
