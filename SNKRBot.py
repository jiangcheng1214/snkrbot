import datetime
import time
from random import random

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains, Proxy
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from utils import log, wait_until, type_with_delay, log_exception, save_page

call_site = 'nikeV4'
size_dropdown_xpath = '//button[@data-qa="size-dropdown"]'
refreshing_xpath = '//div[text()="refresh"]'
sold_out_xpath = '//div[text()="Sold Out"]'
notify_me_xpath = '//button[@data-qa="notify-me-cta"]'
spinner_xpath = '//img[@data-qa="spinner-img"]'
submit_order_xpath = '//button[@data-qa="save-button" and text()="Submit Order"]'
continue_button_xpath = '//button[@data-qa="save-button" and text()="Save & Continue"]'

refresh_wait_time_in_second = 5


# Step 0: fill in payment information and emails

class SNKRConfig:
    def __init__(self, url, size_list, is_debug=False):
        self.url = url
        self.size_list = size_list
        self.is_debug = is_debug


class SNKRBot:

    def __init__(self, chrome_driver_bin_path, email, password, cv_number, SNKRConfigs, release_time, headless,
                 thread_id, proxy=None):
        options = Options()
        # setup userAgent
        software_names = [SoftwareName.CHROME.value]
        operation_systems = [OperatingSystem.WINDOWS.name, OperatingSystem.LINUX.name]
        user_agent_rotator = UserAgent(software_names=software_names, operation_systems=operation_systems, limit=100)
        user_agent = user_agent_rotator.get_random_user_agent()
        options.add_argument(f'user-agent={user_agent}')
        # setup headless mode
        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
        # setup proxy
        capabilities = webdriver.DesiredCapabilities.CHROME
        if proxy:
            p = Proxy()
            p.proxyType = ProxyType.MANUAL
            p.autodetect = False
            p.http_proxy = proxy
            p.ssl_proxy = proxy
            p.socks_proxy = proxy
            p.add_to_capabilities(capabilities)

        options.add_argument("--window-size=1280,1417")
        self.driver = webdriver.Chrome(chrome_driver_bin_path, options=options, desired_capabilities=capabilities)

        self.email = email
        self.password = password
        self.cv_number = cv_number
        self.SNKRConfigs = SNKRConfigs
        self.release_time = release_time
        self.url_results = {}
        self.thread_id = thread_id

    def log(self, string):
        print("[{}][{}] {}".format(self.thread_id, datetime.datetime.now(), string))

    def log_in(self):
        self.driver.get("https://www.nike.com/launch")
        time.sleep(2)
        save_page(self.driver, self.thread_id)
        while not self.driver.find_elements_by_xpath('//span[@data-qa="user-name"]'):
            try:
                WebDriverWait(self.driver, 1).until(expected_conditions.presence_of_element_located(
                    (By.XPATH, '//button[@data-qa="top-nav-join-or-login-button"]')))
                self.log("Login Attempt...")
                save_page(self.driver, self.thread_id)
                if self.driver.find_elements_by_xpath('//button[@data-qa="top-nav-join-or-login-button"]'):
                    self.driver.find_elements_by_xpath('//button[@data-qa="top-nav-join-or-login-button"]')[0].click()
                    self.log("Login button clicked...")
                    save_page(self.driver, self.thread_id)
                else:
                    self.log("Missing: {}".format('//button[@data-qa="top-nav-join-or-login-button"]'))
                    save_page(self.driver, self.thread_id)
                    return False
                WebDriverWait(self.driver, 1).until(
                    expected_conditions.presence_of_element_located((By.XPATH, '//input[@type="email"]')))
                time.sleep(0.5)
                if not type_with_delay(self.driver, '//input[@type="email"]', self.email):
                    return False
                self.log("Email typed.")
                save_page(self.driver, self.thread_id)
                time.sleep(2)
                if not type_with_delay(self.driver, '//input[@type="password"]', self.password):
                    return False
                self.log("Password typed.")
                save_page(self.driver, self.thread_id)
                self.driver.find_elements_by_xpath('//input[@type="password"]')[0].send_keys(Keys.ENTER)
                WebDriverWait(self.driver, 5).until(expected_conditions.presence_of_element_located(
                    (By.XPATH, '//span[@data-qa="user-name"]')))
            except TimeoutException:
                if self.driver.find_elements_by_xpath('//input[@value="Dismiss this error"]'):
                    self.log("Found: {}".format('//input[@value="Dismiss this error"]'))
                    save_page(self.driver, self.thread_id)
                    self.driver.find_elements_by_xpath('//input[@value="Dismiss this error"]')[0].click()
                    self.log("Dismissed: {}".format('//input[@value="Dismiss this error"]'))
                    save_page(self.driver, self.thread_id)
                self.driver.refresh()
                time.sleep(2)
                continue
            except Exception as e:
                log_exception(self.driver, self.thread_id)
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
        save_page(self.driver, self.thread_id)
        for size_element in self.driver.find_elements_by_xpath(size_dropdown_xpath):
            try:
                btn_text = size_element.text
            except Exception as e:
                log_exception(self.driver, self.thread_id)
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
                    save_page(self.driver, self.thread_id)
                    return False
                try:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(size_button).perform()
                except Exception as e:
                    log_exception(self.driver, self.thread_id)
                try:
                    if not self.handle_popup_confirmation():
                        self.log("Failed to handle popup confirmation")
                        return False
                    size_button.click()
                    self.log("Size clicked {}".format(size_button_xpath))
                    return True
                except Exception as e:
                    log_exception(self.driver, self.thread_id)
                    self.log("Failed to click {}".format(size_button_xpath))

                    return False
        self.log("Size not found!")
        return False

    def add_to_cart(self):
        time.sleep(0.1)
        if self.driver.find_elements_by_xpath('//button[@data-qa="add-to-cart"]'):
            self.log("Detected add-to-cart")
            try:
                self.driver.find_elements_by_xpath('//button[@data-qa="add-to-cart"]')[0].click()
                self.log("Clicked '//button[@data-qa='add-to-cart']'")
            except Exception as e:
                log_exception(self.driver, self.thread_id)
                return False
            return True
        elif self.driver.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]'):
            self.log("Detected feed-buy-cta")
            # sorted(d.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]'),key=lambda x: convert_price_text_to_int(x.text), reverse=True)[0].click()
            try:
                buy_button = self.driver.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]')[0]
                actions = ActionChains(self.driver)
                actions.move_to_element(buy_button).perform()
                self.log("moved to buy button")
            except Exception as e:
                log_exception(self.driver, self.thread_id)
                pass
            try:
                time.sleep(0.1)
                buy_button = self.driver.find_elements_by_xpath('//button[@data-qa="feed-buy-cta"]')[0]
                buy_button.click()
                self.log("Clicked '//button[@data-qa='feed-buy-cta']'")
                return True
            except Exception as e:
                log_exception(self.driver, self.thread_id)
                return False
        elif self.driver.find_elements_by_xpath('//button[@type="button" and contains(text(), "Enter Drawing")]'):
            self.log("Detected entering drawing")
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Enter Drawing")]')[0]
                actions = ActionChains(self.driver)
                actions.move_to_element(enter_drawing_button).perform()
            except Exception:
                log_exception(self.driver, self.thread_id)
                pass
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Enter Drawing")]')[0]
                # <button type="button" class="cta-btn u-uppercase cta-btn ncss-btn text-color-white ncss-brand d-sm-b d-lg-ib pr5-sm pl5-sm pt3-sm pb3-sm d-sm-ib bg-black test-buyable buyable-full-width buyable-full-width ">Enter Drawing  $110</button>
                enter_drawing_button.click()
                self.log("Clicked '//button[@type='button' and contains(text(), 'Enter Drawing')]'")
                save_page(self.driver, self.thread_id)
                return True
            except Exception as e:
                log_exception(self.driver, self.thread_id)
                return False
        elif self.driver.find_elements_by_xpath('//button[@type="button" and contains(text(), "Join Draw")]'):
            self.log("Detected join draw")
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Join Draw")]')[0]
                actions = ActionChains(self.driver)
                actions.move_to_element(enter_drawing_button).perform()
            except Exception as e:
                log_exception(self.driver, self.thread_id)
                pass
            try:
                enter_drawing_button = \
                    self.driver.find_elements_by_xpath(
                        '//button[@type="button" and contains(text(), "Join Draw")]')[0]
                # <button type="button" class="cta-btn u-uppercase cta-btn ncss-btn text-color-white ncss-brand d-sm-b d-lg-ib pr5-sm pl5-sm pt3-sm pb3-sm d-sm-ib bg-black test-buyable buyable-full-width buyable-full-width ">Enter Drawing  $110</button>
                enter_drawing_button.click()
                self.log("Clicked '//button[@type='button' and contains(text(), 'Join Draw')]'")
                save_page(self.driver, self.thread_id)
                return True
            except Exception as e:
                log_exception(self.driver, self.thread_id)
                return False

        self.log("No known clickable button after selecting size")
        return False

    def enter_cv_number(self):
        try:
            cv_number_input = self.driver.find_element_by_xpath('//input[@id="cvNumber"]')
            for num in self.cv_number:
                cv_number_input.send_keys(num)
                time.sleep(random() / 10)
            return True
        except Exception:
            self.log("cannot input cv number")
        try:
            self.driver.switch_to.frame(
                self.driver.find_element_by_xpath('//iframe[@sandbox="allow-scripts allow-same-origin"]'))
            cv_number_input = self.driver.find_element_by_xpath('//input[@id="cvNumber"]')
            for num in self.cv_number:
                cv_number_input.send_keys(num)
                time.sleep(random() / 10)
            self.driver.switch_to.default_content()
            return True
        except Exception:
            self.log("cannot input cv number")
        return False

    def enter_payment_information(self):
        try:
            iframe_count = len(
                self.driver.find_elements_by_xpath('//iframe[@sandbox="allow-scripts allow-same-origin"]'))
            self.log("iframe count {}".format(iframe_count))
            if iframe_count < 1:
                self.log("iframe count is 0")
                if self.enter_cv_number():
                    return True
                try:
                    self.driver.find_element_by_xpath('//input[@data-qa="payment-radio"]').click()
                    time.sleep(0.3)
                    if self.enter_cv_number():
                        return True
                except Exception:
                    self.log("cv_number cannot be added after clicking payment-radio")
                try:
                    self.driver.find_element_by_xpath('//span[@data-qa="payment-text"]').click()
                    time.sleep(0.3)
                    if self.enter_cv_number():
                        return True
                except Exception:
                    self.log("cv_number cannot be added after clicking payment-text")
                try:
                    self.driver.find_element_by_xpath('//span[@data-qa="payment-icn"]').click()
                    time.sleep(0.3)
                    if self.enter_cv_number():
                        return True
                except Exception:
                    self.log("cv_number cannot be added after clicking payment-icn")
                return False
            else:
                self.driver.switch_to.frame(
                    self.driver.find_elements_by_xpath('//iframe[@sandbox="allow-scripts allow-same-origin"]')[0])
                self.log("Switched to iframe")
                # if self.driver.find_elements_by_xpath('//input[@id="creditCardNumber"]'):
                #     credit_card_input = self.driver.find_element_by_xpath('//input[@id="creditCardNumber"]')
                #     for num in BOT_INFO["card_number"]:
                #         credit_card_input.send_keys(num)
                #         time.sleep(random() / 10)
                #     expiration_date_input = self.driver.find_element_by_xpath('//input[@id="expirationDate"]')
                #     for num in BOT_INFO["card_expiration"]:
                #         expiration_date_input.send_keys(num)
                #         time.sleep(random() / 10)
                if self.driver.find_elements_by_xpath('//input[@id="cvNumber"]'):
                    self.log("input cvNumber..")
                    cv_number_input = self.driver.find_element_by_xpath('//input[@id="cvNumber"]')
                    self.log("cvNumber :{}".format(self.cv_number))
                    for num in self.cv_number:
                        cv_number_input.send_keys(num)
                        time.sleep(random() / 10)
                    self.log("cvNumber typed!")
                    save_page(self.driver, self.thread_id)
                self.driver.switch_to.default_content()
                self.log("Switched to default content")
                return True
        except Exception:
            self.driver.switch_to.default_content()
            log_exception(self.driver, self.thread_id)
            self.log("Handle payment failed")
            return False

    def handle_pop_out_payment(self):
        time.sleep(1)
        if not self.driver.find_elements_by_xpath(continue_button_xpath):
            self.log("Continue button is not found!")
            return False
        if not self.driver.find_elements_by_xpath(submit_order_xpath):
            self.log("Submit button is not found!")
            return False
        if self.driver.find_elements_by_xpath(
                '//button[@data-qa="save-button" and text()="Save & Continue" and contains(@class, "disabled")]'):
            # Need to enter CV number
            self.log("detected disabled continue button")
            entered_payment = self.enter_payment_information()
            self.log("entered_payment = {}".format(entered_payment))
        i = 0
        while i < len(self.driver.find_elements_by_xpath(continue_button_xpath)):
            self.log("current i = {}".format(i))
            try:
                self.driver.find_elements_by_xpath(continue_button_xpath)[i].click()
                self.log('clicked Save & Continue button i = {}'.format(i))
                break
            except Exception:
                log_exception(self.driver, self.thread_id)
            i += 1
        return True

    def submit_order(self, is_debug):
        self.log("Going to submit order")
        save_page(self.driver, self.thread_id)
        if is_debug:
            self.log("submit order can be clicked!")
            return True
        try:
            # first attempt to click submit
            submit_button = self.driver.find_elements_by_xpath(submit_order_xpath)[0]
            actions = ActionChains(self.driver)
            actions.click(submit_button).perform()
            self.log("Performed click on submit button")
            save_page(self.driver, self.thread_id)
            if self.driver.find_elements_by_xpath('//button[@data-qa="presubmit-confirm"]'):
                self.log("Performed click on double confirm submit button")
                self.driver.find_elements_by_xpath('//button[@data-qa="presubmit-confirm"]')[0].click()
                save_page(self.driver, self.thread_id)
            try:
                WebDriverWait(self.driver, 3).until(
                    expected_conditions.invisibility_of_element_located((By.XPATH, submit_order_xpath)))
                self.log("1st attempt submit button not clickable")
                save_page(self.driver, self.thread_id)
                return True
            except Exception:
                self.log("submit button is still visible!")
                log_exception(self.driver, self.thread_id)
        except Exception:
            self.log("failed to click submit button")
            log_exception(self.driver, self.thread_id)

        try:
            # second attempt to click submit
            submit_button = self.driver.find_elements_by_xpath(submit_order_xpath)[0]
            submit_button.click()
            self.log("Clicked on submit button")
            save_page(self.driver, self.thread_id)
            try:
                WebDriverWait(self.driver, 3).until(
                    expected_conditions.invisibility_of_element_located((By.XPATH, submit_order_xpath)))
                self.log("2nd attempt submit button not clickable")
                save_page(self.driver, self.thread_id)
                return True
            except Exception as e:
                self.log("submit button is still visible!")
                log_exception(self.driver, self.thread_id)
                return False
        except Exception as e:
            self.log("Failed to click submit button")
            log_exception(self.driver, self.thread_id)
            return False

    def handle_popup_confirmation(self):
        if self.driver.find_elements_by_xpath('//a[@class="ncss-btn-primary-dark cta-btn btn-lg"]'):
            self.log("Pop up confirmation detected!")
            save_page(self.driver, self.thread_id)
            try:
                self.driver.find_elements_by_xpath('//a[@class="ncss-btn-primary-dark cta-btn btn-lg"]')[
                    0].click()
                self.log("Pop up window clicked")
                save_page(self.driver, self.thread_id)
                return True
            except Exception:
                log_exception(self.driver, self.thread_id)
                self.log("POPUP WINDOW error")
                return False
        else:
            self.log("Pop up confirmation not detected!")
            return True

    def run(self):
        self.log("start! release time: {}".format(self.release_time))
        # Wait until 1(2) minutes before release time
        wait_until(self.release_time, 120)
        self.log("120 seconds before release time")
        while 1:
            self.log("LOG IN started!")
            if self.log_in():
                self.log("LOG IN Finished!")
                break
        wait_until(self.release_time, 60)
        save_page(self.driver, self.thread_id)
        self.log("60 seconds before release time")
        # Open one tab for one product:
        for i in range(len(self.SNKRConfigs)):
            try:
                url = self.SNKRConfigs[i].url
                if i == 0:
                    self.driver.get(url)
                else:
                    self.driver.execute_script("window.open('{}');".format(url))
                time.sleep(0.5)
            except Exception:
                log_exception(self.driver, self.thread_id)
        wait_until(self.release_time, 30)
        self.log("release time!")
        # Keep looping all window tabs
        retry = {}
        while len(self.url_results) < len(self.SNKRConfigs):
            for i in range(len(self.SNKRConfigs)):
                self.driver.switch_to.window(self.driver.window_handles[i])
                if i in self.url_results:
                    continue
                url = self.SNKRConfigs[i].url
                if url not in retry:
                    retry[url] = 0
                try:
                    time.sleep(0.5)
                    if self.driver.find_elements_by_xpath(spinner_xpath):
                        self.log("spinner is detected.")
                    WebDriverWait(self.driver, 10).until(
                        expected_conditions.invisibility_of_element_located((By.XPATH, spinner_xpath)))
                    if self.driver.find_elements_by_xpath(spinner_xpath):
                        self.log("spinner is gone.")
                    time.sleep(0.5)
                    if self.driver.find_elements_by_xpath(sold_out_xpath):
                        # sold out (after 15 mins)
                        seconds_since_release = (datetime.datetime.now() - self.release_time).total_seconds()
                        if seconds_since_release > 60 * 15:
                            self.log("SOLD OUT at:{}".format(url))
                            save_page(self.driver, self.thread_id)
                            self.url_results[i] = "SOLD OUT"
                            break
                    elif self.driver.find_elements_by_xpath(notify_me_xpath):
                        self.log("Still waiting.. at:{}".format(url))
                        save_page(self.driver, self.thread_id)
                        self.driver.refresh()
                        continue
                    elif self.driver.find_elements_by_xpath(spinner_xpath):
                        self.log("Still spinning.. at:{}".format(url))
                        save_page(self.driver, self.thread_id)
                        continue
                    elif not self.driver.find_elements_by_xpath(size_dropdown_xpath):
                        self.log("Size list is not available.. at:{}".format(url))
                        save_page(self.driver, self.thread_id)
                        self.driver.refresh()
                        continue
                except TimeoutException:
                    self.log("waiting for first spinner time out..")
                    if self.driver.find_elements_by_xpath(
                            '//pre[@style="word-wrap: break-word; white-space: pre-wrap;" and contains(text(), "Forbidden access")]'):
                        self.log("IP access blocked")
                        self.url_results[i] = "Forbidden access"
                        save_page(self.driver, self.thread_id)
                    log_exception(self.driver, self.thread_id)
                    retry[url] += 1
                    if retry[url] > 1:
                        self.log("time out > 2 times, refreshing..")
                        self.driver.refresh()
                        retry[url] = 0
                    continue

                # size drop list is available
                should_select_size = True
                if self.driver.find_elements_by_xpath('//button[@data-qa="save-button"]'):
                    # handle the case where size selection can be skipped (should be after a previous failure)
                    self.log("Detected payment pop out before selecting size")
                    save_page(self.driver, self.thread_id)
                    should_select_size = False
                if should_select_size:
                    for size in self.SNKRConfigs[i].size_list:
                        self.log("Size: {}".format(size))
                        if self.select_size(size):
                            break
                    save_page(self.driver, self.thread_id)

                should_click_buy_button = True
                if self.driver.find_elements_by_xpath('//button[@data-qa="save-button"]'):
                    # handle the case where click buy button can be skipped (should be after a previous failure)
                    self.log("Detected payment pop out before clicking buy")
                    save_page(self.driver, self.thread_id)
                    should_click_buy_button = False

                if should_click_buy_button:
                    if not self.add_to_cart():
                        self.log("failed to click buy button")
                        save_page(self.driver, self.thread_id)
                        self.driver.refresh()
                        continue

                try:
                    if not self.handle_popup_confirmation():
                        self.url_results[i] = "POPUP WINDOW"
                        break
                    WebDriverWait(self.driver, 1).until(expected_conditions.presence_of_element_located(
                        (By.XPATH, '//button[@data-qa="save-button"]')))
                    self.log("Detected payment pop out")
                    WebDriverWait(self.driver, 5).until(expected_conditions.presence_of_element_located(
                        (By.XPATH, '//section[@class="section-layout border-top completed"]')))
                    self.log("Detected payment pop out fully loaded")
                    WebDriverWait(self.driver, 5).until(expected_conditions.invisibility_of_element_located(
                        (By.XPATH, '//img[@data-qa="spinner-img"]')))
                    self.log("Detected spinner is gone")
                    self.log("Detected cv number input box: {}".format(len(
                        self.driver.find_elements_by_xpath('//iframe[@sandbox="allow-scripts allow-same-origin"]'))))
                    save_page(self.driver, self.thread_id)
                    if not self.handle_pop_out_payment():
                        self.log("payment not handled! refreshing")
                        save_page(self.driver, self.thread_id)
                        self.driver.refresh()
                        continue
                    is_debug = self.SNKRConfigs[i].is_debug
                    if self.submit_order(is_debug):
                        self.url_results[i] = "SUCCESS"
                        for i in range(6):
                            time.sleep(5)
                            save_page(self.driver, self.thread_id)
                        self.log("Finished checkout")
                        break
                    else:
                        self.log("Failed to checkout! refreshing")
                        save_page(self.driver, self.thread_id)
                        self.driver.refresh()
                except TimeoutException:
                    if self.driver.find_elements_by_xpath(
                            '//div[text()="VERIFY YOUR MOBILE NUMBER"]') and self.driver.find_elements_by_xpath(
                        '//input[@class="phoneNumber"]'):
                        self.log("Verify mobile number pop out!")
                        self.url_results[i] = "VERIFY YOUR MOBILE NUMBER"
                        break
                    self.log("payment pop out is not detected")
                    save_page(self.driver, self.thread_id)
                    self.driver.refresh()
                    continue
        log("RESULTS - {}: {}".format(self.thread_id, self.url_results))
