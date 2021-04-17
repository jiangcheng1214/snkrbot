import datetime
import json
import os
import threading

from SNKRBot import SNKRBot
from utils import log

'''
Onetime setup
1. Log into nike account and make sure a) payment info and b) shipping info are properly setup (IMPORTANT!)
2. Update info/information.json with account information (see information_example.json) 
3. Install chrome driver and update local path -> CHROMEDRIVER_BIN_PATH
'''

# Step
CHROMEDRIVER_BIN_PATH = '/usr/local/bin/chromedriver'
BOT_INFO = json.loads(open(os.path.dirname(os.path.abspath(__file__)) + '/info/information.json', "r").read())


class SNKRThreadedBot(threading.Thread):
    def __init__(self, chrome_driver_bin_path, SNKRConfigs, email, password, cv_number, release_time, headless, thread_id, proxy=None):
        threading.Thread.__init__(self)
        self.bot = SNKRBot(chrome_driver_bin_path, email, password, cv_number, SNKRConfigs, release_time, headless, thread_id, proxy)
        self.email = email

    def run(self):
        log("Starting {}".format(self.email))
        self.bot.run()


class SNKRConfig:
    def __init__(self, url, size_list, is_debug=False):
        self.url = url
        self.size_list = size_list
        self.is_debug = is_debug


# Step 1 - update date (time shouldn't need to be changed.)
release_time = datetime.datetime(2021, 4, 16, 7, 0)

# Step 2 - update nike snkrs link and preferred sizes (convert to US men for women only sneakers)
SNKRConfigs = [
    SNKRConfig("https://www.nike.com/launch/t/air-more-uptempo-black-and-varsity-red", ['10'], is_debug=False),
    SNKRConfig("https://www.nike.com/launch/t/womens-dunk-low-green-glow", ['7.5'], is_debug=False),
]

threads = []

for ind in range(len(BOT_INFO)):
    t = SNKRThreadedBot(chrome_driver_bin_path=CHROMEDRIVER_BIN_PATH, SNKRConfigs=SNKRConfigs, email=BOT_INFO[ind]["email"],
                        password=BOT_INFO[ind]["password"], cv_number=BOT_INFO[ind]["cv_number"],
                        release_time=release_time,
                        headless=False, thread_id=ind)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

log("All threads done!")
