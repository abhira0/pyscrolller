import argparse
import datetime as dt
import json
import os
import random
import shutil
import threading
import time
from sys import path_importer_cache

import pandas as pd
import requests
from bs4 import BeautifulSoup
from praw.models.listing.mixins import submission
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from termcolor import cprint

from utils import *


class utils(utils):
    def updateUltimatum(ultimatum: dict, sub_name: str):
        _dir = os.getcwd()
        path = _dir + f"\\{sub_name}.json"
        if os.path.exists(path):
            ultimatum.update(utils.jsonLoad(path))

    def joinThread(thread_list):
        if type(thread_list) == type([]):
            for i in thread_list:
                i.join()
        else:
            thread_list.join()


class Downloader:
    def over_18_button(self, driver):
        driver.find_element_by_css_selector(".nsfw-warning__accept-button").click()

    def welcome_pop(self, driver):
        driver.find_element_by_css_selector(".notification__title").click()

    def scroll(self, driver, last_height, add_height):
        new_height = last_height + add_height
        driver.execute_script(
            f"window.scrollTo(0, {new_height});"
        )  # Scroll down to bottom
        return new_height

    def cssFindAttr(self, item, selector: str, attribute: str) -> str:
        temp = item.find_element_by_css_selector(selector).get_attribute(attribute)
        return temp

    def cssFind(self, item, selector: str):
        temp = item.find_elements_by_css_selector(selector)
        return temp

    def moveTo(self, driver, element):
        ActionChains(driver).move_to_element(element).perform()
        time.sleep(0.1)

    def ultimatumPut(self, ultimatum, url, typ, title, media_links):
        ultimatum.update(
            {url: {"type": typ, "title": title, "media_links": media_links}}
        )

    def getContentCount(self, typ):
        count = 0
        for i, j in self.ultimatum.items():
            if j["type"] == typ:
                count += 1
        return count

    def screen_dim(self):
        screen_width = self.driver.execute_script("return screen.width")
        screen_height = self.driver.execute_script("return screen.height")
        return screen_width, screen_height

    def screen_resize(self, div_width: int, mul_height: int) -> int:
        screen_width, screen_height = self.screen_dim()
        d_screen_width = screen_width // div_width
        d_screen_height = screen_height * mul_height
        self.driver.set_window_size(d_screen_width, d_screen_height)
        return screen_height

    def begin(self, sort_key):
        self.num_of_ele = self.getContentCount(self.typ)
        scrape_url = (
            f"https://scrolller.com/r/{self.sub_name}?filter={self.typ}&sort={sort_key}"
        )
        state = State(f"{str(self.typ).upper()}: {scrape_url}", False)
        state.openURL(scrape_url)
        utils.tryExcept(self.welcome_pop, [state.driver], 10)
        utils.tryExcept(self.over_18_button, [state.driver], 10)
        time.sleep(3)
        self.driver = state.driver
        self.scrapeAll()
        self.driver.close()


class Picture(Downloader):
    typ = "pictures"

    def __init__(self, sub_name: str, ultimatum: dict) -> None:
        """A class dedicated to scrape pictures links by applying pictures filter to the url

        Args:
            sub_name (str): Name of the subreddit
            ultimatum (dict): The ultimate dictionary used to save the scraped data.
        """
        self.ultimatum = ultimatum
        self.sub_name = sub_name

    def scrapeAll(self):
        screen_height = self.screen_resize(1, 3)
        height = self.scroll(self.driver, 0, 0)
        stop_flag = max(int(self.num_of_ele * 2), 500)
        while stop_flag > 0:
            ret = self.getLinksFromWindow()
            stop_flag = stop_flag - ret if ret else max(int(self.num_of_ele * 2), 500)
            height = self.scroll(self.driver, height, screen_height * 2)

    def getMetadata(self, img_item) -> tuple:
        src = self.cssFindAttr(img_item, "img", "srcset").split(",")[-1].split(" ")[0]
        title = self.cssFindAttr(img_item, ".item-panel__description", "innerHTML")
        return title, src

    def getLinksFromWindow(self):
        c_already_present = 0
        c_added = 0
        for img_item in self.cssFind(self.driver, ".vertical-view__item"):
            try:
                url = self.cssFindAttr(img_item, "a[rel=nofollow]", "href")
                if url not in self.ultimatum.keys():
                    self.moveTo(self.driver, img_item)
                    title, src = self.getMetadata(img_item)
                    self.ultimatumPut(self.ultimatum, url, "pictures", title, [src])
                    c_added += 1
                    self.num_of_ele += 1
                else:
                    c_already_present += 1
                print(f"ULTIMATUM [{len(self.ultimatum)}]", end="\r")
            except Exception as e:
                # print(e)
                ...
        # return 0 if at least one link is added to ultimatum
        return c_already_present if c_added == 0 else 0


class Video(Downloader):
    typ = "videos"

    def __init__(self, sub_name: str, ultimatum: dict) -> None:
        """A class dedicated to scrape videos links by applying video filter to the url

        Args:
            sub_name (str): Name of the subreddit
            ultimatum (dict): The ultimate dictionary used to save the scraped data.
        """
        self.ultimatum = ultimatum
        self.sub_name = sub_name

    def scrapeAll(self):
        screen_height = self.screen_resize(2, 3)
        height = self.scroll(self.driver, 0, 0)
        stop_flag = max(int(self.num_of_ele * 2), 500)
        while stop_flag > 0:
            ret = self.getLinksFromWindow()
            if ret == "EXIT52":
                return
            stop_flag = stop_flag - ret if ret else max(int(self.num_of_ele * 2), 500)
            height = self.scroll(self.driver, height, screen_height * 2)

    def getMetadata(self, item) -> tuple:
        source_tags = self.cssFind(item, "video source")
        src = source_tags[-1].get_attribute("src")
        title = self.cssFindAttr(item, "div.item-panel__description", "innerHTML")
        return title, src

    def getLinksFromWindow(self):
        c_already_present = 0
        c_added = 0
        cols = self.cssFind(self.driver, ".vertical-view__column")
        for col in cols:
            if "Can't find any" in self.driver.page_source:
                return "EXIT52"
            items = self.cssFind(col, ".vertical-view__item")
            for item in items:
                try:
                    url = self.cssFindAttr(item, "a", "href")
                    if url not in self.ultimatum.keys():
                        item = WebDriverWait(self.driver, 10).until(lambda x: item)
                        self.moveTo(self.driver, item)
                        title, src = self.getMetadata(item)
                        self.ultimatumPut(self.ultimatum, url, "videos", title, [src])
                        c_added += 1
                        self.num_of_ele += 1
                    else:
                        c_already_present += 1
                    print(f"ULTIMATUM [{len(self.ultimatum)}]", end="\r")
                except:
                    ...
        # return 0 if at least one link is added to ultimatum
        return c_already_present if c_added == 0 else 0


class Album(Downloader):
    ...


class pyscrolller:
    ultimatum = {}
    save_flag = True
    info_dikt = {"downloading": 0, "thread_list": [], "downloaded": 0, "existing": 0}

    def __init__(self, sub_name) -> None:
        self.sub_name = sub_name
        utils.makedir(f"{os.getcwd()}\\scrollls")
        utils.makedir(f"{os.getcwd()}\\scrollls\\{sub_name}")
        path_ = f"{os.getcwd()}\\scrollls\\{self.sub_name}\\{self.sub_name}.json"
        if os.path.exists(path_):
            self.ultimatum = utils.jsonLoad(path_)

    def spawnThreads(self, loop_till, class_obj, thread_list):
        sorts_ = ["top", "hot", "new", "rising"]
        for i in range(loop_till):
            sort_key = sorts_[i if i < 4 else 4]
            instance_ = class_obj(self.sub_name, self.ultimatum)
            thr = threading.Thread(target=instance_.begin, args=(sort_key,))
            thread_list.append(thr)
            thr.start()

    def begin(self):
        utils.updateUltimatum(self.ultimatum, sub_name)
        save_thread = threading.Thread(target=self.damnSave)
        save_thread.start()
        thread_list = []
        self.spawnThreads(4, Picture, thread_list)
        self.spawnThreads(4, Video, thread_list)
        self.spawnThreads(0, Album, thread_list)
        utils.joinThread(thread_list)
        self.quit_damnSave(save_thread)

    def downloadAll(self):
        save_thread = threading.Thread(target=self.damnSave)
        save_thread.start()
        for typ in ["pictures", "videos", "albums"][1:]:
            self.downloadAllType(typ)
        self.quit_damnSave(save_thread)

    def downloadAllType(self, typ):
        path_ = f"{os.getcwd()}\\scrollls\\{self.sub_name}\\media"
        utils.makedir(path_)
        # rand_ultimatum = sorted(self.ultimatum.items(), key=lambda x: random.random())
        rand_ultimatum = self.ultimatum.items()
        for scrolller_url, media_ele in rand_ultimatum:
            if typ != media_ele["type"]:
                continue
            d = "d_media"
            ml = "media_links"
            # self.ultimatum[scrolller_url][d] = []
            self.ultimatum[scrolller_url][d] = self.ultimatum[scrolller_url].get(d, [])
            su = scrolller_url
            rem = list(set(self.ultimatum[su][ml]) - (set(self.ultimatum[su][d])))
            for media in rem:
                args = (media, path_, scrolller_url, media_ele["title"])
                thr = threading.Thread(target=self.downloadMedia, args=args)
                self.info_dikt["thread_list"].append(thr)
                thr.start()
                while len(self.info_dikt["thread_list"]) > 50:
                    for thread_ in self.info_dikt["thread_list"]:
                        if not thread_.is_alive():
                            thread_.join()
                            self.info_dikt["thread_list"].remove(thread_)
        for i in self.info_dikt["thread_list"]:
            i.join()

    def downloadMedia(self, url, _dir, _id, title=None):
        try:
            self.downloadAMedia(url, _dir, _id, title)
        except:
            cprint(f"❗ Connection error while downloading", "red", end="")
            cprint(f"'{url}'", "magenta")

    def downloadAMedia(self, url, _dir, _id, title):
        url_filename, ex10sion = url.split("/")[-1].split(".")
        downloaded = False
        ex10sion = ex10sion.split("?")[0] if "?" in ex10sion else ex10sion
        red_id = _id.split("-")[-1].split(".")[0]
        if title:
            title = utils.replace_chars(title, '<>:"/\|?*.', "")
            path_ = f"{_dir}\\{title}-{red_id}.{ex10sion}"
        else:
            path_ = f"{_dir}\\{url_filename}-{red_id}.{ex10sion}"
        r = requests.get(url, stream=True)
        try:
            file_size = str(os.path.getsize(path_)).strip()
            if r.headers["Content-Length"].strip() == str(file_size):
                cprint(f"\t[+] Existing media", "green", end="")
                cprint(f"'{url[:40]}'", "magenta")
                utils.clearPrint()
                downloaded = True
        except Exception as e:
            # print(e)
            ...
            # cprint(f"❗- {e}", "red", end="")
            # cprint(f"'{_id}'", "magenta")
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(path_, "wb") as f:
                shutil.copyfileobj(r.raw, f)
            if url not in self.ultimatum[_id]["d_media"]:
                downloaded = True
            cprint(f"[+] Downloaded media from", "green", end="")
            cprint(f" '{url}'", "magenta")

        if downloaded:
            self.ultimatum[_id]["d_media"].append(url)
            self.ultimatum[_id]["d_media"] = list(set(self.ultimatum[_id]["d_media"]))
        else:
            cprint(f"❗ {r.status_code} Error while downloading", "red", end="")
            cprint(f"'{url}'", "magenta")

    def damnSave(self):
        while self.save_flag:
            try:
                self.saveIt()
                time.sleep(10)
            except Exception as e:
                ...

    def saveIt(self):
        path_ = f"{os.getcwd()}\\scrollls\\{self.sub_name}\\{self.sub_name}.json"
        with open(path_, "w") as f:
            json.dump(self.ultimatum, f, indent=4)

    def quit_damnSave(self, save_thread):
        self.saveIt()
        self.save_flag = False
        utils.joinThread(save_thread)


def argsParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-killff", help="Kill firefox instances", action="store_true")
    parser.add_argument(
        "-justkillff", help="Just kill firefox instances", action="store_true"
    )
    return parser.parse_args()


sub_name = "skinnyfit"
args = argsParser()
utils.killproc("firefox.exe") if args.killff else None
if args.justkillff:
    utils.killproc("firefox.exe")
    exit(0)

pyscr = pyscrolller(sub_name)
pyscr.begin()
# pyscr.downloadAll()
