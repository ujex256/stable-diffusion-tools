import hashlib
import pathlib
from io import BytesIO
from pathlib import Path
import requests
from tqdm.auto import tqdm


MODELS = {
    "Counterfeit-V2.5": {
        "dw_url": {
            "full": {
                "url": "https://huggingface.co/gsdf/Counterfeit-V2.5/resolve/main/Counterfeit-V2.5.safetensors",
                "sha256": "bd83b90a2e50d26ded19b6bf0d7319ece2e1c26c6d352c41d25bfc1a1585aebb",
            },
            "pruned": {
                "url": "https://huggingface.co/gsdf/Counterfeit-V2.5/resolve/main/Counterfeit-V2.5_pruned.safetensors",
                "sha256": "a074b8864e31b8681e40db3dfde0005df7b5309fd2a2f592a2caee59e4591cae",
            },
            "fp16": {
                "url": "https://huggingface.co/gsdf/Counterfeit-V2.5/resolve/main/Counterfeit-V2.5_fp16.safetensors",
                "sha256": "71e703a0fca0e284dd9868bca3ce63c64084db1f0d68835f0a31e1f4e5b7cca6",
            },
            "fp32": None,
        },
        "readme": "https://huggingface.co/gsdf/Counterfeit-V2.5/blob/main/README.md",
        "vae": "https://huggingface.co/gsdf/Counterfeit-V2.5/resolve/main/Counterfeit-V2.5.vae.pt",
    },
    "anything-V3": {
        "dw_url": {
            "full": {
                "url": "https://huggingface.co/Linaqruf/anything-v3.0/resolve/main/anything-v3-full.safetensors",
                "sha256": "abcaf14e5acb8023c79c3901f8ffc04eb3c646d7793f3b36a439bf09e32868cd",
            },
            "pruned": None,
            "fp16": {
                "url": "https://huggingface.co/Linaqruf/anything-v3.0/resolve/main/anything-v3-fp16-pruned.safetensors",
                "sha256": "d1facd9a2b7c5e46d4d54de5a7441c370804c0c5727ca04a0708319d04047c58",
            },
            "fp32": {
                "url": "https://huggingface.co/Linaqruf/anything-v3.0/resolve/main/anything-v3-fp32-pruned.safetensors",
                "sha256": "308884898741f81f4dbe32a7806a26c28b594d8ea21310fbed5c5dcecff6aa32",
            },
        },
        "readme": "https://huggingface.co/Linaqruf/anything-v3.0/blob/main/README.md",
        "vae": None,
    },
}
ENBEDDIGS = {}
VAE = {}
LORA = {}




def download_model(url, path, sha256: str | None = None):
    file_size = int(requests.head(url, allow_redirects=True).headers["Content-Length"])

    if isinstance(path, str):
        fe = open(path, "wb")
    elif isinstance(path, Path):
        fe = path.open("wb")
    else:
        fe = path
    with fe as f:
        pbar = tqdm(total=file_size, unit="B", unit_scale=True, dynamic_ncols=True)
        for chunk in requests.get(url, stream=True).iter_content(chunk_size=1024):
            f.write(chunk)
            pbar.update(len(chunk))
        pbar.close()
        hash = hashlib.sha256(f.getvalue()).hexdigest()
    if isinstance(sha256, str) and sha256 != hash:
        raise Exception("ハッシュが違う")

if __name__ == "__main__":
    by = BytesIO()
    ta = MODELS["Counterfeit-V2.5"]["dw_url"]["fp16"]
    aaa = download_model(ta["url"], by, sha256=ta["sha256"])

    path = Path.cwd()
    if p := list(path.glob("stable-diffusion-webui")):
        path = list(filter(lambda x: x.is_dir(), p))[0]
    elif path.name == "stable-diffusion-webui":
        pass
    else:
        path = Path(input())
        if not path.exists():
            raise FileNotFoundError(f"The directory {path.absolute()} does not exist.")
        if not path.is_dir():
            raise Exception(f"Inputted path \"{path.absolute()}\" is not directory.")

    print(path.absolute())
