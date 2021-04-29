import os
import json

p = f"{os.getcwd()}\\scrollls\\IndianBabes\\IndianBabes.json"

with open(p, "r") as f:
    dikt = json.load(f)


info = {}
actual = {}
for i, j in dikt["albums"].items():
    x = j.get("downloaded", [])
    y = j.get("mediaUrls")
    typ = j.get("type")
    actual["total"] = actual.get("total", 0) + 1
    actual[typ] = actual.get(typ, 0) + 1
    if set(y) - set(x) == set():
        info["total"] = info.get("total", 0) + 1
        info[typ] = info.get(typ, 0) + 1

print(info)
for i, j in info.items():
    print(f"{i}: {j}/{actual[i]}  \tRemaining: {actual[i] - j}")


album_media_count = 0
album_count = len(dikt["albums"])
media_count = len(dikt["medias"])
video_count = len([i for j in dikt["medias"] for i in j["mediaUrl"]])
image_count = 0
print(video_count)