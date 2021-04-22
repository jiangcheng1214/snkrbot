import datetime
import json
import os
import threading

from SNKRBot import SNKRBot, SNKRConfig
from utils import log

'''
Onetime setup
1. Log into nike account and make sure a) payment info and b) shipping info are properly setup (IMPORTANT!)
2. Update info/information.json with account information (see information_example.json) 
3. Install chrome driver and update local path -> CHROMEDRIVER_BIN_PATH

Setup for next SNKRs drop
1. Update info/config.json with account information (see config_example.json)
'''

# Step
CHROMEDRIVER_BIN_PATH = '/usr/local/bin/chromedriver'
BOT_INFO = json.loads(open(os.path.dirname(os.path.abspath(__file__)) + '/info/information.json', "r").read())
BOT_CONFIG = json.loads(open(os.path.dirname(os.path.abspath(__file__)) + '/info/config.json', "r").read())


class SNKRThreadedBot(threading.Thread):
    def __init__(self, chrome_driver_bin_path, SNKRConfigs, email, password, cv_number, release_time, headless,
                 thread_id, proxy=None):
        threading.Thread.__init__(self)
        self.bot = SNKRBot(chrome_driver_bin_path, email, password, cv_number, SNKRConfigs, release_time, headless,
                           thread_id, proxy)
        self.email = email

    def run(self):
        log("Starting {}".format(self.email))
        self.bot.run()


date = BOT_CONFIG['drop_date'].split('/')
release_time = datetime.datetime(int(date[0]), int(date[1]), int(date[2]), 7, 0)
SNKRConfigs = [SNKRConfig(item['link'], item['sizes'], item['is_debug']) for item in BOT_CONFIG['drop_list']]

threads = []

for ind in range(len(BOT_INFO)):
    t = SNKRThreadedBot(chrome_driver_bin_path=CHROMEDRIVER_BIN_PATH, SNKRConfigs=SNKRConfigs,
                        email=BOT_INFO[ind]["email"],
                        password=BOT_INFO[ind]["password"], cv_number=BOT_INFO[ind]["cv_number"],
                        release_time=release_time,
                        headless=False, thread_id=ind)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

log("All threads done!")
