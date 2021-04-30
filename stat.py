import os
import json, argparse
from termcolor import cprint


def getStat(p):
    with open(p, "r") as f:
        dikt = json.load(f)

    count_album = len(dikt["albums"])
    d_album = []
    d_album_media = []
    for i, iv in dikt["albums"].items():
        m__ = set(iv["mediaUrls"] if iv["mediaUrls"] else [])
        d__ = set(iv["downloaded"] if iv["downloaded"] else [])
        d_album_media.extend(iv["downloaded"])
        diff = m__ - d__
        if not diff:
            d_album.append(i)
    count_d_album = len(d_album)
    count_album_media = len(
        [i for j, jv in dikt["albums"].items() for i in jv["mediaUrls"]]
    )
    count_d_album_media = len(
        [i for j, jv in dikt["albums"].items() for i in jv["downloaded"]]
    )

    count_picsvids = len(dikt["medias"])
    downloaded_picsvids = [
        iv["mediaUrl"] for i, iv in dikt["medias"].items() if iv["downloaded"]
    ]
    count_d_picsvids = len(downloaded_picsvids)

    all_media = [i for j, jv in dikt["albums"].items() for i in jv["mediaUrls"]] + [
        iv["mediaUrl"] for i, iv in dikt["medias"].items()
    ]
    count_all_media = len(all_media)

    all_d_media = downloaded_picsvids + d_album_media
    count_all_d_media = len(all_d_media)
    count_ex10sion = {}
    for i in all_media:
        x10 = i.split(".")[-1]
        count_ex10sion[x10] = count_ex10sion.get(x10, 0) + 1
    count_d_x10sion = {}
    for i in all_d_media:
        x10 = i.split(".")[-1]
        count_d_x10sion[x10] = count_d_x10sion.get(x10, 0) + 1

    cprint("--------Albums--------", "cyan")
    print("Downloaded Albums      : ", end="")
    cprint(f"{count_d_album}/{count_album}", "green", end="")
    cprint(f"\t{count_album-count_d_album} albums", "red")
    print("Downloaded Album Medias: ", end="")
    cprint(f"{count_d_album_media}/{count_album_media}", "green", end="")
    cprint(f"\t{count_album_media-count_d_album_media} medias", "red")
    cprint("--------Medias--------", "cyan")
    print("Downloaded Medias      : ", end="")
    cprint(f"{count_d_picsvids}/{count_picsvids}", "green", end="")
    cprint(f"\t{count_picsvids-count_d_picsvids} medias", "red")
    cprint("------All Media-------", "cyan")
    print("Downloaded Medias      : ", end="")
    cprint(f"{count_all_d_media}/{count_all_media}", "green", end="")
    cprint(f"\t{count_all_media-count_all_d_media} medias", "red")
    for i, j in count_ex10sion.items():
        try:
            k = count_d_x10sion[i]
        except:
            k = 0
        cprint(f"{i}: ", "magenta", end="")
        cprint(f"{k}/{j}", "green", end="")
        cprint(f"\t{j-k} medias", "red")


def argsParser():
    parser = argparse.ArgumentParser(
        description="Scraper for https://www.scrolller.com"
    )
    parser.add_argument("-s", "--subname", help="Name of the subreddit", required=True)
    return parser.parse_args()


args = argsParser()
p = f"{os.getcwd()}\\scrollls\\{args.subname}\\{args.subname}.json"
getStat(p)