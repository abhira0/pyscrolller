import json
import os
import shutil
import threading
import time

import requests
import argparse
from mods.utils import duocprint as dcprint
from mods.utils import utils

GBL_stop_quering_RESET = 500
GBL_media_POST_threads = 30
GBL_album_POST_threads = 30
GBL_download_threads = 50


class utils(utils):
    def updateUltimatum(ultimatum: dict, sub_name: str) -> None:
        """Updates the current state of the ultimatum
        Args:
            ultimatum (dict): Dictionary to be updated
            sub_name (str): Name of the subreddit
        """
        _dir = os.getcwd()
        path = _dir + f"\\{sub_name}.json"
        if os.path.exists(path):
            ultimatum.update(utils.jsonLoad(path))

    def joinThread(thread_list: list) -> None:
        """Performs join operation on all the threads present in given thread_list
        Args:
            thread_list (list): List of threads to be joined
        """
        if type(thread_list) == type([]):
            for i in thread_list:
                i.join()
        else:
            thread_list.join()


class Downloader:
    def download(self):
        save_thread = threading.Thread(target=self.damnSave)
        save_thread.start()
        utils.makedir(f"{self.cwd}\\scrollls\\{self.sub_name}\\media")
        self.downloading_threads = []
        self.sema4 = threading.BoundedSemaphore(GBL_download_threads)
        if not args.na:
            self.downloadAlbums()
        self.downloadPicsVids()
        utils.joinThread(self.downloading_threads)
        self.quit_damnSave(save_thread)

    def downloadAlbums(self):
        for album_url, album_info in self.ultimatum["albums"].items():
            media_set = set(album_info["mediaUrls"] if album_info["mediaUrls"] else [])
            downloaded_set = set(
                album_info["downloaded"] if album_info["downloaded"] else []
            )
            diff_list = media_set - downloaded_set
            if diff_list == []:
                continue
            thr = threading.Thread(
                target=self.downloadAnAlbum,
                args=(
                    album_url,
                    album_info,
                    diff_list,
                ),
            )
            thr.start()
            self.downloading_threads.append(thr)

    def downloadAnAlbum(self, album_url, album_info, diff_list):
        sub_folder = album_info["title"]
        __path = f"{self.cwd}\\scrollls\\{self.sub_name}\\media\\{sub_folder}"
        utils.makedir(__path)
        for media_url in diff_list:
            self.sema4.acquire()
            if self.downloadMedia(media_url, __path):
                tmp_dict = album_info["downloaded"]
                tmp_dict.append(media_url)
                tmp_dict = list(set(tmp_dict if tmp_dict else []))
                self.ultimatum["albums"][album_url]["downloaded"] = tmp_dict

    def downloadPicsVids(self):
        u_media = self.ultimatum["medias"]
        for parent_url, media_info in u_media.items():
            if u_media[parent_url]["downloaded"]:
                continue
            self.sema4.acquire()
            thr = threading.Thread(
                target=self.downloadAPicVid,
                args=(
                    parent_url,
                    media_info,
                ),
            )
            thr.start()
            self.downloading_threads.append(thr)

    def downloadAPicVid(self, parent_url, media_info):
        sub_folder = None
        title = media_info["title"]
        _id = parent_url.split("-")[-1].strip()
        media_url = media_info["mediaUrl"]
        __path = f"{self.cwd}\\scrollls\\{self.sub_name}\\media"
        if self.downloadMedia(media_url, __path, _id, title):
            self.ultimatum["medias"][parent_url]["downloaded"] = True

    def downloadMedia(self, url, _dir, _id=None, title=None):
        try:
            return self.downloadAMedia(url, _dir, _id, title)
        except Exception as e:
            print(e)
            dcprint(f"❗ Connection error while downloading ", f"'{url}'", "r", "m")
            return False

    def downloadAMedia(self, url, _dir, _id, title):
        url_filename, ex10sion = url.split("/")[-1].split(".")
        downloaded = False
        ex10sion = ex10sion.split("?")[0] if "?" in ex10sion else ex10sion
        if title:
            path_ = f"{_dir}\\{title}-{_id}.{ex10sion}"
        else:
            path_ = f"{_dir}\\{url_filename}.{ex10sion}"
        r = requests.get(url, stream=True)
        try:
            file_size = str(os.path.getsize(path_)).strip()
            if r.headers["Content-Length"].strip() == str(file_size):
                dcprint(f"\t[+] Existing media", f"'{url[:40]}'", "g", "m")
                utils.clearPrint()
                downloaded = True
        except:
            ...
        if r.status_code == 200 and not downloaded:
            r.raw.decode_content = True
            with open(path_, "wb") as f:
                shutil.copyfileobj(r.raw, f)
            downloaded = True
            dcprint(f"[+] Downloaded media from ", f"'{url}'", "g", "m")

        if not downloaded:
            dcprint(f"❗ {r.status_code} Error while downloading ", f"'{url}'", "r", "m")
        self.sema4.release()
        return downloaded


class pyscrolller(Downloader):
    post_url = "https://api.scrolller.com/api/v2/graphql"
    ultimatum = {"albums": {}, "medias": {}}
    save_flag = True  # used by a deamon which saves the ultimatum periodically
    media_len = 0
    album_len = 0

    def __init__(self, sub_name: str) -> None:
        """Class instantiation
        Args:
            sub_name (str): Name of the subreddit
        """
        self.sub_name = sub_name
        self.cwd = os.getcwd()
        utils.makedir(f"{self.cwd}\\scrollls")
        utils.makedir(f"{self.cwd}\\scrollls\\{self.sub_name}")
        path_ = f"{self.cwd}\\scrollls\\{self.sub_name}\\{self.sub_name}.json"
        if os.path.exists(path_):
            self.ultimatum = utils.jsonLoad(path_)

    def begin(self):
        save_thread = threading.Thread(target=self.damnSave)
        save_thread.start()
        self.threadSubreddit()
        self.media_len = len(self.ultimatum["medias"])
        self.album_len = len(self.ultimatum["albums"])
        self.threadAlbums()
        self.quit_damnSave(save_thread)

    def threadSubreddit(self):
        self.stop_quering = max(GBL_stop_quering_RESET, len(self.ultimatum["medias"]))
        sema4 = threading.BoundedSemaphore(GBL_media_POST_threads)
        thread_list = []
        while True:
            sema4.acquire()
            if self.stop_quering <= 0:
                break
            thr = threading.Thread(target=self.processSubResponse, args=(sema4,))
            thr.start()
            thread_list.append(thr)
        utils.joinThread(thread_list)

    def threadAlbums(self):
        sema4 = threading.BoundedSemaphore(GBL_album_POST_threads)
        thread_list = []
        for album_url in self.ultimatum["albums"].keys():
            sema4.acquire()
            args = tuple([album_url, sema4])
            thr = threading.Thread(target=self.processAlbResponse, args=args)
            thr.start()
            thread_list.append(thr)
        utils.joinThread(thread_list)
        __al_in_len = len(
            [i for i, j in self.ultimatum["albums"].items() if j["mediaUrls"] != []]
        )
        print(f"ULTIMATUM [{self.album_len}[{__al_in_len}],{self.media_len}]")

    def processSubResponse(self, sema4) -> int:
        children_items = self.querySubreddit()
        new_entity = 0
        for child in children_items:
            albumUrl, url = child["albumUrl"], child["url"]
            title = utils.cleanPathName(child["title"])
            if albumUrl and (albumUrl not in self.ultimatum["albums"].keys()):
                tmp_dict = {"title": title, "mediaUrls": [], "downloaded": []}
                self.ultimatum["albums"][albumUrl] = tmp_dict
                new_entity += 1
            elif url not in self.ultimatum["medias"].keys():
                mediaUrl = child["mediaSources"][-1]["url"]
                tmp_dict = {"title": title, "mediaUrl": mediaUrl, "downloaded": False}
                self.ultimatum["medias"][url] = tmp_dict
                new_entity += 1
        __al_len = len(self.ultimatum["albums"])
        __me_len = len(self.ultimatum["medias"])
        print(f"ULTIMATUM [{__al_len},{__me_len}]", end="\r")
        time.sleep(0.2)
        if new_entity == 0:
            self.stop_quering -= (len(children_items)) - new_entity
        else:
            self.stop_quering = max(
                GBL_stop_quering_RESET, len(self.ultimatum["medias"])
            )
        sema4.release()

    def querySubreddit(self):
        __subreddit_query = {
            "query": "query SubredditQuery( $url: String! $filter: SubredditPostFilter $iterator: String ) { getSubreddit(url: $url) { children( limit: 100 iterator: $iterator filter: $filter ) { iterator items { __typename url title subredditTitle subredditUrl redditPath isNsfw albumUrl isFavorite mediaSources { url width height isOptimized } } } } }",
            "variables": {"url": f"/r/{self.sub_name}", "filter": None},
            "authorization": None,
        }
        response_obj = requests.post(self.post_url, json=__subreddit_query)
        response_json = json.loads(response_obj.text)
        children_items = response_json["data"]["getSubreddit"]["children"]["items"]
        return children_items

    def processAlbResponse(self, album_url, sema4):
        children_items = self.queryAlbum(album_url)
        media_link_list = [i["mediaSources"][-1]["url"] for i in children_items]
        self.ultimatum["albums"][album_url]["mediaUrls"] = media_link_list
        __al_in_len = len(
            [i for i, j in self.ultimatum["albums"].items() if j["mediaUrls"] != []]
        )
        print(f"ULTIMATUM [{self.album_len}[{__al_in_len}],{self.media_len}]", end="\r")
        sema4.release()

    def queryAlbum(self, album_url):
        __album_query = {
            "query": "query AlbumQuery( $url: String! $iterator: String ) { getAlbum(url: $url) { __typename url title isComplete isNsfw redditPath children( iterator: $iterator limit: 50 ) { iterator items { __typename mediaSources { url width height isOptimized } } } } }",
            "variables": {"url": album_url},
            "authorization": None,
        }
        response_obj = requests.post(self.post_url, json=__album_query)
        response_json = json.loads(response_obj.text)
        children_items = response_json["data"]["getAlbum"]["children"]["items"]
        return children_items

    def damnSave(self, time_period: float = 5) -> None:
        """Calls the saveIt() to saves the ultimatum periodically
        Args:
            time_period (float, optional): Periodicity in seconds. Defaults to 10.
        """
        # Function quits as soon as the self.save_flag is unset
        while self.save_flag:
            try:
                self.saveIt()
                time.sleep(time_period)
            except Exception as e:
                ...

    def saveIt(self) -> None:
        """Saves the ultimatum dictionary with all the scraped information locally to hard drive"""
        path_ = f"{os.getcwd()}\\scrollls\\{self.sub_name}\\{self.sub_name}.json"
        with open(path_, "w") as f:
            json.dump(self.ultimatum, f, indent=4)

    def quit_damnSave(self, save_thread: threading.Thread) -> None:
        """Makes the daemon which saves the ultimatum periodically quit when scraping is done
        Args:
            save_thread (threading.Thread): The thread which needed to be terminated
        """
        self.saveIt()
        self.save_flag = False
        utils.joinThread(save_thread)


def argsParser():
    parser = argparse.ArgumentParser(
        description="Scraper for https://www.scrolller.com"
    )
    parser.add_argument("-s", "--subname", help="Name of the subreddit", required=True)
    parser.add_argument(
        "-d",
        "--download",
        help="Download after scraping the links",
        action="store_true",
    )
    parser.add_argument(
        "-h",
        "--harvest",
        help="Harvest all the links of medias to download as the next step",
        action="store_true",
    )
    parser.add_argument(
        "-na", help="Do not download Albums (No Albums)", action="store_true"
    )
    parser.add_argument(
        "-nm",
        help="Do not download Pics and Videos which are not in any albums (No Media)",
        action="store_true",
    )
    return parser.parse_args()


args = argsParser()
sc = pyscrolller(args.subname)
if sc.harvest:
    sc.begin()
if args.download:
    sc.download()
