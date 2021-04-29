import argparse
import json
import os
import shutil
import threading
import time

import requests
from termcolor import cprint

from mods.trio import Album, Picture, Video
from mods.utils import utils


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
        # sorts_ = ["random"] * 10
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
        self.spawnThreads(1, Picture, thread_list)
        self.spawnThreads(1, Video, thread_list)
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
