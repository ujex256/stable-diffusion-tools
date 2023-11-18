import hashlib
import pathlib
import re
import math
from io import BytesIO
from pathlib import Path
import requests
from tqdm.auto import tqdm


def download_model(url: str, path: str | pathlib.Path | BytesIO, sha256: str | None = None):
    resp_resp = requests.head(url, allow_redirects=True)
    file_size = int(resp_resp.headers["Content-Length"])
    file_name = extract_file_name(resp_resp)
    print(file_name)

    if isinstance(path, str):
        fe = pathlib.Path(path).joinpath(file_name).open("wb")
    elif isinstance(path, Path):
        fe = path.joinpath(file_name).open("wb")
    elif isinstance(BytesIO, path):
        fe = path
    else:
        raise ValueError("Arg \"path\" must be string or pathlib.Path or BytesIO.")

    with fe as f:
        pbar = tqdm(
            total=file_size, dynamic_ncols=True,
            unit="B", unit_scale=True, unit_divisor=1024
        )
        for chunk in requests.get(url, stream=True).iter_content(chunk_size=1024):
            f.write(chunk)
            pbar.update(len(chunk))
        pbar.close()
    # TODO: xxhashつかう
    #     hash = hashlib.sha256(f.getvalue()).hexdigest()
    # if isinstance(sha256, str) and sha256 != hash:
    #     raise Exception("ハッシュが違う")


def extract_file_name(r: requests.Response):
    if "Content-Disposition" in r.headers:
        return re.findall("filename=\"(.+)\"", r.headers["Content-Disposition"])[0].rstrip(";")
    else:
        return r.url.split("/")[-1].split("?")[0]


def remove_filesize_string(string: str) -> str:
    return re.sub(r"\([^()]*\)$", "", string).rstrip(" ")


def generate_size_str(url: str) -> str:
    if url.startswith("https://civitai.com"):
        url = "https://civitai.com/api/v1/model-versions/" + url.split("/")[6].split("?")[0]
        byte_count = round(float(requests.get(url).json()["files"][0]["sizeKB"]) * 1024)
    else:
        resp_header = requests.head(url, allow_redirects=True)
        byte_count = int(resp_header.headers["Content-Length"])

    # from: https://pystyle.info/python-data-size-conversion/
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB")
    i = math.floor(math.log(byte_count, 1024)) if byte_count > 0 else 0
    byte_count = round(byte_count / 1024 ** i, 2)
    return f"{byte_count} {units[i]}"
