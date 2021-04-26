import os

p = f"{os.getcwd()}\\scrollls\\IndianBabes\\IndianBabes.json"
import json

with open(p, "r") as f:
    d = json.load(f)


info = {}
actual = {}
for i, j in d.items():
    x = j.get("d_media", [])
    y = j.get("media_links")
    typ = j.get("type")
    actual["total"] = actual.get("total", 0) + 1
    actual[typ] = actual.get(typ, 0) + 1
    if set(y) - set(x) == set():
        info["total"] = info.get("total", 0) + 1
        info[typ] = info.get(typ, 0) + 1

for i, j in info.items():
    print(f"{i}: {j}/{actual[i]}  \tRemaining: {actual[i] - j}")