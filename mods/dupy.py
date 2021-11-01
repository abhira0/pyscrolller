import hashlib, os

from pyrhd.utility.utils import Utils


class Dupy:
    def __init__(self, root_path) -> None:
        self.main(root_path)

    def getHash(self, file_path, first_chunk_only=True) -> str:
        with open(file_path, "rb") as f:
            file_data = f.read(1024 if first_chunk_only else None)
            hashed = hashlib.sha1(file_data).digest().hex()
        return hashed

    def main(self, root_path):
        hm = dict()
        # size based hashmap
        for i in Utils.os.getAllFiles(root_path):
            file_size = os.path.getsize(i)
            hm[file_size] = hm.get(file_size, {0: [], 1: {}, 2: {}})
            hm[file_size][0].append(i)

        # first 1024 bytes based hashmap
        for i, j in ((i, j) for (i, j) in hm.items() if len(j[0]) > 1):
            for file_path in j[0]:
                hashed = self.getHash(file_path)
                hm[i][1][hashed] = hm[i][1].get(hashed, [])
                hm[i][1][hashed].append(file_path)

        # full-file based hashmap
        for i, j in hm.items():
            for a, b in j[1].items():
                for file_path in b:
                    hashed = self.getHash(file_path, False)
                    hm[i][2][hashed] = hm[i][2].get(hashed, [])
                    hm[i][2][hashed].append(file_path)

        # analysis
        for size, size_based in hm.items():
            for file_hash, file_based in size_based[2].items():
                for del_file in file_based[:-1]:
                    os.remove(del_file)
                    print(f"Removing {del_file}")
        cache_path = os.path.join(root_path, "dupy.json")
        Utils.json.saveDict(hm, cache_path)


Dupy("../scrollls/CelebrityPokies")
