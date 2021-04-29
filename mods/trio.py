import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from mods.utils import State, utils


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
