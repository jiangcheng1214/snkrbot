import datetime
import json
import os
import threading
import time
from random import random

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from utils import log, wait_until, type_with_delay, log_exception, save_page, wait_until_clickable, wait_until_invisible

call_site = 'nikeV4'
size_dropdown_xpath = '//button[@data-qa="size-dropdown"]'
refreshing_xpath = '//div[text()="refresh"]'
sold_out_xpath = '//div[text()="Sold Out"]'
notify_me_xpath = '//button[@data-qa="notify-me-cta"]'
spinner_xpath = '//img[@data-qa="spinner-img"]'
submit_order_xpath = '//button[@data-qa="save-button" and text()="Submit Order"]'
continue_button_xpath = '//button[@data-qa="save-button" and text()="Save & Continue"]'

NIKE_CHECKOUT_URL = "https://www.nike.com/checkout"

# Step 0: fill in payment information and emails

BOT_INFO = json.loads(open(os.path.dirname(os.path.abspath(__file__)) + '/info/information.json', "r").read())


class NikeBot:

    def __init__(self, email, password, cv_code, url_size_metadata_list, start_time, headless, thread_id):
        options = Options()
        options.add_argument("--window-size=2560,1417")
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=options)
        self.email = email
        self.password = password
        self.cv_number = cv_code
        self.url_size_metadata_list = url_size_metadata_list
        self.start_time = start_time
        self.window_index_list_list = []
        self.url_wait_time_map = {}
        self.waiting_time_list = [3, 5]
        self.url_results = {}
        self.thread_id = thread_id

    def log(self, string):
        print("[{}][{}] {}".format(self.thread_id, datetime.datetime.now(), string))

    def log_in(self):
        self.driver.get("https://www.nike.com/launch")
        time.sleep(2)
        while not self.driver.find_elements_by_xpath('//span[@data-qa="user-name"]'):
            try:
                WebDriverWait(self.driver, 1).until(expected_conditions.presence_of_element_located(
                    (By.XPATH, '//button[@data-qa="top-nav-join-or-login-button"]')))
                if self.driver.find_elements_by_xpath('//button[@data-qa="top-nav-join-or-login-button"]'):
                    self.driver.find_elements_by_xpath('//button[@data-qa="top-nav-join-or-login-button"]')[0].click()
                else:
                    self.log("Missing: {}".format('//button[@data-qa="top-nav-join-or-login-button"]'))
                    return False
                WebDriverWait(self.driver, 1).until(
                    expected_conditions.presence_of_element_located((By.XPATH, '//input[@type="email"]')))
                time.sleep(0.5)
                if self.driver.find_elements_by_xpath('//input[@name="keepMeLoggedIn"]'):
                    self.driver.find_elements_by_xpath('//input[@name="keepMeLoggedIn"]')[0].send_keys(' ')
                if not type_with_delay(self.driver, '//input[@type="email"]', self.email):
                    return False
                time.sleep(2)
                if not type_with_delay(self.driver, '//input[@type="password"]', self.password):
                    return False
                time.sleep(1)
                self.driver.find_elements_by_xpath('//input[@type="password"]')[0].send_keys(Keys.ENTER)
                WebDriverWait(self.driver, 5).until(expected_conditions.presence_of_element_located(
                    (By.XPATH, '//span[@data-qa="user-name"]')))
            except TimeoutException:
                if self.driver.find_elements_by_xpath('//input[@value="Dismiss this error"]'):
                    self.log("Found: {}".format('//input[@value="Dismiss this error"]'))
                    self.driver.find_elements_by_xpath('//input[@value="Dismiss this error"]')[0].click()
                    self.log("Dismissed: {}".format('//input[@value="Dismiss this error"]'))
                self.driver.refresh()
                time.sleep(2)
                continue
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                return False
        return True

    def select_size(self, target_size):
        def is_right_size(button_text, size_text):
            if button_text == size_text:
                return True
            no_space_text = button_text.replace(' ', '')
            for text in no_space_text.split('/'):
                if text == size_text:
                    return True
                if "M" in text and text[1:] == size_text:
                    return True
            return False

        self.log("Looking for size:{}".format(target_size))
        save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
        for size_element in self.driver.find_elements_by_xpath(size_dropdown_xpath):
            try:
                btn_text = size_element.text
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                continue
            self.log("Current size text {}".format(btn_text))
            if is_right_size(btn_text, target_size):
                self.log("Right size {}".format(btn_text))
                size_button_xpath = '//button[@data-qa="size-dropdown" and text()="{}"]'.format(
                    btn_text)
                size_button = self.driver.find_element_by_xpath(size_button_xpath)
                if not size_button:
                    self.log("size_button is None")
                    return False
                if size_button.get_attribute("disabled"):
                    self.log("size_button is disabled")
                    save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                    return False
                try:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(size_button).perform()
                except Exception as e:
                    log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                try:
                    size_button.click()
                    self.log("Size clicked {}".format(size_button_xpath))
                    return True
                except Exception as e:
                    log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                    self.log("Failed to click {}".format(size_button_xpath))
                    return False
        self.log("Size not found!")
        return False

    def add_to_cart(self):
        if self.driver.find_elements_by_xpath('//button[@data-qa="add-to-cart"]'):
            try:
                self.driver.find_elements_by_xpath('//button[@data-qa="add-to-cart"]')[0].click()
                self.log("Clicked '//button[@data-qa='add-to-cart']'")
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                return False
            return True
        elif self.driver.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]'):
            try:
                buy_button = self.driver.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]')[0]
                actions = ActionChains(self.driver)
                actions.move_to_element(buy_button).perform()
                self.log("moved to buy button")
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                pass
            try:
                time.sleep(0.1)
                buy_button = self.driver.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]')[0]
                buy_button.click()
                self.log("Clicked '//button[@data-qa='feed-buy-cta']'")
                return True
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                return False
        elif self.driver.find_elements_by_xpath('//button[@type="button" and contains(text(), "Enter Drawing")]'):
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Enter Drawing")]')[0]
                actions = ActionChains(self.driver)
                actions.move_to_element(enter_drawing_button).perform()
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                pass
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Enter Drawing")]')[0]
                # <button type="button" class="cta-btn u-uppercase cta-btn ncss-btn text-color-white ncss-brand d-sm-b d-lg-ib pr5-sm pl5-sm pt3-sm pb3-sm d-sm-ib bg-black test-buyable buyable-full-width buyable-full-width ">Enter Drawing  $110</button>
                enter_drawing_button.click()
                self.log("Clicked '//button[@type='button' and contains(text(), 'Enter Drawing')]'")
                time.sleep(2)
                save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                return True
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                return False
        elif self.driver.find_elements_by_xpath('//button[@type="button" and contains(text(), "Join Draw")]'):
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Join Draw")]')[0]
                actions = ActionChains(self.driver)
                actions.move_to_element(enter_drawing_button).perform()
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                pass
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Join Draw")]')[0]
                # <button type="button" class="cta-btn u-uppercase cta-btn ncss-btn text-color-white ncss-brand d-sm-b d-lg-ib pr5-sm pl5-sm pt3-sm pb3-sm d-sm-ib bg-black test-buyable buyable-full-width buyable-full-width ">Enter Drawing  $110</button>
                enter_drawing_button.click()
                self.log("Clicked '//button[@type='button' and contains(text(), 'Join Draw')]'")
                time.sleep(2)
                save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                return True
            except Exception as e:
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                return False

        self.log("No known clickable button after selecting size")
        return False

    def enter_security_code_if_needed(self):
        if self.driver.find_elements_by_xpath('//p[text()="Please re-enter a security code:"]'):
            iframe_count = len(
                self.driver.find_elements_by_xpath('//iframe[@sandbox="allow-scripts allow-same-origin"]'))
            self.log("iframe count {}".format(iframe_count))
            if iframe_count == 1:
                self.driver.switch_to.frame(
                    self.driver.find_elements_by_xpath('//iframe[@sandbox="allow-scripts allow-same-origin"]')[0])
                self.log("Switched to iframe")
                if self.driver.find_elements_by_xpath('//input[@id="cvNumber"]'):
                    cv_number_input = self.driver.find_element_by_xpath('//input[@id="cvNumber"]')
                    for num in self.cv_number:
                        cv_number_input.send_keys(num)
                        time.sleep(random() / 10)
                self.driver.switch_to.default_content()
                self.log("Switched to default content")

    def click_place_order_button(self):
        try:
            xpath = "//button[text()='Place Order']"
            wait_until_clickable(self.driver, xpath=xpath, duration=10)
            self.driver.find_element_by_xpath(xpath).click()
            save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
            wait_until_invisible(self.driver, xpath=xpath, duration=10)
            save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
        except Exception as e:
            log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))

    def submit_order(self, should_buy):
        self.log("Going to submit order")
        save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
        if should_buy:
            try:
                # first attempt to click submit
                submit_button = self.driver.find_elements_by_xpath(submit_order_xpath)[0]
                actions = ActionChains(self.driver)
                actions.click(submit_button).perform()
                self.log("Performed click on submit button")
                save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                try:
                    WebDriverWait(self.driver, 3).until(
                        expected_conditions.invisibility_of_element_located((By.XPATH, submit_order_xpath)))
                    self.log("1st attempt submit button not clickable")
                    save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                    return True
                except Exception as e:
                    self.log("submit button is still visible!")
                    log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
            except Exception as e:
                self.log("failed to click submit button")
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))

            try:
                # second attempt to click submit
                submit_button = self.driver.find_elements_by_xpath(submit_order_xpath)[0]
                submit_button.click()
                self.log("Clicked on submit button")
                save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                try:
                    WebDriverWait(self.driver, 3).until(
                        expected_conditions.invisibility_of_element_located((By.XPATH, submit_order_xpath)))
                    self.log("2nd attempt submit button not clickable")
                    save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                    return True
                except Exception as e:
                    self.log("submit button is still visible!")
                    log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                    return False
            except Exception as e:
                self.log("Failed to click submit button")
                log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                return False
        else:
            self.log("submit order can be clicked!")
            return True

    def run(self):
        self.log("run!")
        wait_until(self.start_time)
        while 1:
            self.log("LOG IN started!")
            if self.log_in():
                self.log("LOG IN Finished!")
                break
        for url_index in range(len(self.url_size_metadata_list)):
            self.window_index_list_list.append([])
            for i in self.waiting_time_list:
                try:
                    url = self.url_size_metadata_list[url_index][0]
                    self.driver.execute_script("window.open('{}');".format(url))
                    time.sleep(0.5)
                    window_index = len(self.driver.window_handles) - 1
                    self.window_index_list_list[url_index].append(window_index)
                    self.url_wait_time_map[window_index] = datetime.datetime.now()
                    self.log("New window opened url:{} index:{}".format(url, window_index))
                except Exception as e:
                    log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))

        while len(self.url_results) < len(self.url_size_metadata_list):
            for url_index in range(len(self.url_size_metadata_list)):
                window_index_list = self.window_index_list_list[url_index]
                for window_index in window_index_list:
                    if url_index in self.url_results:
                        break
                    url = self.url_size_metadata_list[url_index][0]
                    try:
                        self.driver.switch_to.window(self.driver.window_handles[window_index])
                    except Exception as e:
                        log_exception(e, self.driver, "{} - {}".format(call_site, self.thread_id))
                    if self.driver.find_elements_by_xpath(sold_out_xpath):
                        save_page(self.driver, "{} - {}".format(call_site, self.thread_id))
                        log("url: {} SOLD OUT".format(url))
                        self.url_results[url_index] = "SOLD OUT"
                        break

                    try:
                        WebDriverWait(self.driver, 5).until(
                            expected_conditions.presence_of_element_located((By.XPATH, size_dropdown_xpath)))
                        time.sleep(0.5)
                        self.log("URL:{} Window:{} detected size selectable:{}".format(url, window_index, len(
                            self.driver.find_elements_by_xpath(size_dropdown_xpath))))
                    except Exception:
                        if self.driver.find_elements_by_xpath(spinner_xpath):
                            self.log("URL:{} Spinning..".format(url))
                        elif self.driver.find_elements_by_xpath(notify_me_xpath):
                            self.log("URL:{} Still not launched..".format(url))
                        elif self.driver.find_elements_by_xpath(refreshing_xpath):
                            self.log("URL:{} Refreshing..".format(url))
                        if (datetime.datetime.now() - self.url_wait_time_map[window_index]).total_seconds() > \
                                self.waiting_time_list[window_index % len(self.waiting_time_list)]:
                            self.url_wait_time_map[window_index] = datetime.datetime.now()
                            self.log("Refresh now")
                            self.driver.refresh()
                        continue
                    for size in self.url_size_metadata_list[url_index][1]:
                        self.log("Size: {}".format(size))
                        if self.select_size(size):
                            break
                    if not self.add_to_cart():
                        self.url_wait_time_map[window_index] = datetime.datetime.now()
                        self.log("Refresh now after adding cart failure")
                        self.driver.refresh()
                    else:
                        self.driver.get(NIKE_CHECKOUT_URL)
                    self.enter_security_code_if_needed()
                    should_buy = self.url_size_metadata_list[url_index][2]
                    if should_buy:
                        self.click_place_order_button()
        log("RESULTS - {}: {}".format(self.thread_id, self.url_results))


class MyThread(threading.Thread):
    def __init__(self, url_size_metadata_list, email, password, cv_code, start_time, headless, thread_id):
        threading.Thread.__init__(self)
        self.bot = NikeBot(email, password, cv_code, url_size_metadata_list, start_time, headless, thread_id)
        self.name = "{} - {}".format(email, url_size_metadata_list)

    def run(self):
        log("Starting {}".format(self.name))
        self.bot.run()


url_size_metadata_list = [
    ("https://www.nike.com/launch/t/womens-dunk-low-coast", ['7.5'], True),
    ("https://www.nike.com/launch/t/dunk-low-hyper-cobalt", ['7.5'], True),
    ("https://www.nike.com/launch/t/dunk-low-medium-grey", ['7.5'], True),
    ("https://www.nike.com/launch/t/air-huarache-st%C3%BCssy-desert-oak", ['7.5'], True),
    # ("https://www.nike.com/launch/t/air-force-1-1-cosmic-clay", ['M6'], True),
]  # step 1: fill in right product information
start_run_time = datetime.datetime(2021, 2, 18, 6, 59)  # step 2: fill in right date

threads = []
for ind in range(len(BOT_INFO["credentials"])):
    t = MyThread(url_size_metadata_list=url_size_metadata_list, email=BOT_INFO["credentials"][ind]["email"],
                 password=BOT_INFO["credentials"][ind]["password"], cv_code=BOT_INFO["credentials"][ind]["cv_code"],
                 start_time=start_run_time,
                 headless=False, thread_id=ind)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

log("All threads done!")
