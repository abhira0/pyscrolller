import json
import os
import sys
import time

import psutil
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from termcolor import cprint


class utils:
    @staticmethod
    def tryWait(
        function_name,
        argz: list,
        timeout: int,
        desc: str = None,
        verbose=True,
    ):
        """[summary]

        Args:
            function_name (function): The function object which needed to be tried
            argz (list): The arguments that must be passed to the function
            timeout (int): Maximum timeout in seconds
            desc (str): Description that needed to be printed inside the verbose line
            verbose (bool, optional): Boolean value which turns the verbose mode on. Defaults to True.

        Returns:
            object: Any object returned by the function
        """
        for _ in range(timeout):
            try:
                return_objs = function_name(*argz)
                if return_objs:
                    return return_objs
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
        if verbose:
            cprint(f"❗ Function execution failed for '{desc}' @ {function_name}", "red")

    # Tries for given time and returns the return_object on success
    @staticmethod
    def tryExcept(function_name, argz: list, timeout: int, desc=None, verbose=True):
        """Tries for given time and returns tries_left on success"""
        for i in range(timeout):
            try:
                function_name(*argz)
                return timeout - i - 1
            except:
                time.sleep(1)
        if verbose:
            cprint(f"❗ Function execution failed for '{desc}' @ {function_name}", "red")

    @staticmethod
    def replace_chars(name: str, keywords: str, to: str):
        for i in keywords:
            name = name.replace(i, to)
        return name

    @staticmethod
    def makedir(path: str, verbose=False):
        if not os.path.exists(path):
            os.mkdir(path)
            if verbose:
                cprint(f"\t✅  Directory created : '{path}'", "green")
        elif verbose:
            cprint(f"\t❎  Directory existed : '{path}'", "cyan")

    @staticmethod
    def killproc(name: str):
        cprint(f"[i] Killing all the {name} instances", "cyan")
        print()
        count = 0
        for p in psutil.process_iter():
            try:
                if p.name() == name:
                    count += 1
                    utils.clearPrint()
                    cprint(f" |-> ", "white", attrs=["blink"], end="")
                    cprint(f"Killed [", "green", end="")
                    cprint(f"{count}", "yellow", end="")
                    cprint(f"] instances of {p.name()} ", "green")
                    p.kill()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cprint(f"\n |-> Access Denied while killing {p.name()}", "red")
                continue
            except psutil.NoSuchProcess:
                continue
        if count == 0:
            utils.clearPrint()
            cprint(f" |-> ", "white", attrs=["blink"], end="")
            cprint(f"There was none.", "cyan", end="")
            cprint(f" FUNCTION_ABORT!", "red", end="\n")

    @staticmethod
    def clearPrint():
        CURSOR_UP_ONE = "\x1b[1A"
        ERASE_LINE = "\x1b[2K"
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)

    @staticmethod
    def jsonLoad(path: str):
        with open(path, "r") as f:
            JSON = json.load(f)
            cprint(f" |> ", "cyan", attrs=["blink"], end="")
            cprint(f"[i] Retriving {len(JSON)} links from ", "cyan", end="")
            cprint(f"{path}", "magenta")
        return JSON

    @staticmethod
    def updateUltimatum(ultimatum: dict, sub_name: str):
        _dir = os.getcwd() + "\\media\\" + sub_name
        path = _dir + f"\\{sub_name}.json"
        if os.path.exists(path):
            ultimatum.update(utils.jsonLoad(path))


class State:
    def __init__(self, description, headless=True) -> None:
        gecko_path = r"E:\Downloads\IDM\Compressed\geckodriver.exe"
        opts = Options()
        opts.headless = headless
        # opts.set_preference("permissions.default.image", 2)
        # opts.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
        cprint(f"\t[i] Instantiating a headless Firefox: '{description}'", "cyan")
        self.driver = webdriver.Firefox(executable_path=gecko_path, options=opts)

    def openURL(self, url):
        self.driver.get(url=url)


class Downloader:
    class Site:
        @staticmethod
        def redgifs(url, verbose=True):
            try:
                r = requests.get(url)
                if r.status_code != 200 and verbose:
                    cprint(f"❗ Status Code :{r.status_code} for", "red", end="")
                    cprint(f" '{url}'", "magenta")
                soup = BeautifulSoup(r.content, "html.parser")
                sel = soup.select("video source")
                src = sel[1].get("src")
                return src
            except:
                return None

        @staticmethod
        def gfycat(url, verbose=True):
            try:
                r = requests.get(url)
                if r.status_code != 200 and verbose:
                    cprint(f"❗ Status Code :{r.status_code} for", "red", end="")
                    cprint(f" '{url}'", "magenta")
                soup = BeautifulSoup(r.content, "html.parser")
                sel = soup.select("#mp4Source")
                if sel:
                    src = sel[0].get("src")
                    return src
                else:
                    src = soup.select("video source")[1].get("src")
                    return src
            except:
                return None

        @staticmethod
        def imgur(url, verbose=True):
            state = State(f"Site - {url}")

            def over_18_button():
                state.driver.find_element_by_css_selector("div.Wall-Button").click()

            try:
                state.openURL(url)
                utils.tryExcept(over_18_button, [], 10)
                media = utils.tryWait(
                    state.driver.find_elements_by_css_selector,
                    [".image-placeholder"],
                    3,
                    url,
                    verbose,
                )
                src = media[0].get_attribute("src")
                state.driver.close()
                return src
            except Exception as e:
                print(e)
                state.driver.close()

    class Album:
        @staticmethod
        def imgur(url, verbose=True):
            state = State(f"Album - {url}")

            def over_18_button():
                state.driver.find_element_by_css_selector("div.Wall-Button").click()

            try:
                state.openURL(url)
                utils.tryExcept(over_18_button, [], 10, url, verbose)
                media = utils.tryWait(
                    state.driver.find_elements_by_css_selector,
                    ["div.Gallery-MainContainer div div div div.imageContainer img"],
                    8,
                    url,
                    verbose,
                )
                media_links = [i.get_attribute("src") for i in media]
                cprint(f"[+] Getting links from imgur album:", "blue", end="")
                cprint(f" {url}", "magenta")
                state.driver.close()
                return list(set(media_links))
            except Exception as e:
                if verbose:
                    cprint(f"❗ {e}", "red")
                state.driver.close()
