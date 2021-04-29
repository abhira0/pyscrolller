import json
import threading

import requests

from mods.utils import utils


class pyscrolller:
    post_url = "https://api.scrolller.com/api/v2/graphql"
    ultimatum = {"albums": {}, "medias": {}}
    save_flag = True  # used by a deamon which saves the ultimatum periodically

    def __init__(self, sub_name: str) -> None:
        self.sub_name = sub_name
    def begin(self):
        save_thread = threading.Thread(target=self.damnSave)
        save_thread.start()
        self.getAllLinks()
        self.quit_damnSave()
        
    def getAllLinks(self):
        
    
    def processResponse(self):
        children_items = self.querySubreddit()
        for child in children_items:
            albumUrl = child["albumUrl"]
            url = child["url"]
            title = utils.cleanPathName(child["title"])
            if albumUrl and (url not in self.ultimatum["albums"].keys()):
                self.ultimatum["albums"][url] = {
                    "title": title,
                    "mediaUrls": [],
                    "downloaded": [],
                }
            else:
                mediaUrl = child["mediaSources"][-1]["url"]
                tmp_dict = {"title": title, "mediaUrls": mediaUrl, "downloaded": []}
                self.ultimatum["medias"][url] = tmp_dict

    def spawnNRequests(self):
        ...

    def querySubreddit(self):
        __subreddit_query = {
            "query": "query SubredditQuery( $url: String! $filter: SubredditPostFilter $iterator: String ) { getSubreddit(url: $url) { children( limit: 100 iterator: $iterator filter: $filter ) { iterator items { __typename url title subredditTitle subredditUrl redditPath isNsfw albumUrl isFavorite mediaSources { url width height isOptimized } } } } }",
            "variables": {"url": f"/r/{sub_name}", "filter": None},
            "authorization": None,
        }
        response_obj = requests.post(post_url, json=__subreddit_query)
        response_json = json.loads(response_obj.text)
        children_items = response_json["data"]["getSubreddit"]["children"]["items"]
        return children_items
    
    def damnSave(self, time_period: float = 10) -> None:
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
