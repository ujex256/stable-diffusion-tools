from PIL import Image

from datetime import datetime as dt  # バキバキ
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint


class SDImage:
    def __init__(self, path) -> None:
        self.img_path = Path(path)
        self.image = Image.open(self.img_path)
        self.description = self.image.info

        self.time = FileTime(self.img_path)

    def print_info(self):
        pprint(self.to_dict(), sort_dicts=False)

    def to_dict(self, lower_key: bool = False):
        if hasattr(self, "_d"):
            if lower_key:
                return dict(map(lambda x: (x[0].lower(), x[1]), self._d.items()))
            return self._d

        info: list[str] = self.description["parameters"].split("\n")
        result = dict()
        result["Prompt"] = info[0].rstrip(" ")
        result["Negative_prompt"] = info[1].strip("Negative prompt: ")

        datas = info[2].split(", ")
        attrs = ["Steps", "Sampler", "CFG scale", "Seed", "Size", "Model hash", "Model", "VAE hash", "VAE", "Clip skip", "TI hashes", "Version"]
        for index, attr in enumerate(attrs):
            name = attr.replace(" ", "_")
            elem = datas[index].strip(attr + ": ")
            try:
                elem = float(elem)
                if elem.is_integer():
                    elem = int(elem)
            except ValueError:
                pass
            result[name] = elem
        self._d = result
        if lower_key:
            return dict(map(lambda x: (x[0].lower(), x[1]), result.items()))
        return result

    @property
    def prompt(self):
        return self.to_dict()["Prompt"]

    @property
    def negative_prompt(self):
        return self.to_dict()["Negative_prompt"]

    @property
    def model(self):
        return self.to_dict()["Model"]

    @property
    def seed(self):
        return self.to_dict()["Seed"]

    @property
    def sd_ver(self):
        return self.to_dict()["Version"]


class FileTime:
    def __init__(self, path: Path) -> None:
        self._p = path
        self.ctime = dt.fromtimestamp(self._p.stat().st_ctime)
        self.mtime = dt.fromtimestamp(self._p.stat().st_mtime)


if __name__ == "__main__":
    s = SDImage("../sample.png")
    s.print_info()
    print(s.time.ctime)
