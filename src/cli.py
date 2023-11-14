import json
import argparse
import platform
from pathlib import Path
from os.path import expanduser
from enum import Enum

import questionary as que
import requests

import utils
import cli_validator as validators


class ModelType(Enum):
    CHECKPOINT = "CheckPoint"
    CKPT = "CheckPoint"
    VAE = "VAE"
    EMBEDDINGS = "Embeddings"
    LORA = "LoRA"

    @classmethod
    def cast(cls, string: str):
        TYPES = [cls.CHECKPOINT, cls.VAE, cls.EMBEDDINGS, cls.LORA]
        TYPES_STR = list(map(lambda x: x.value.lower(), TYPES))
        if string.lower() not in TYPES_STR:
            return None
        return TYPES[TYPES_STR.index(string.lower())]

    def dir_name(self):
        return "iaaa"


class MainCLI:
    def __init__(self, config_dir: str | Path, first_time: bool = True) -> None:
        self._config = CLIConfig(config_dir)
        self.parser = argparse.ArgumentParser("Stable Diffusion Tools")
        self.is_first_time = first_time
        self.add_parser()

    def add_parser(self):
        self.actparser = self.parser.add_subparsers(title="action", description="Do action", required=True)

        dw = self.actparser.add_parser("download", aliases=["dw", "dwm"], help="モデルをダウンロードします。")
        dw.set_defaults(func=self.download_model)
        self.actparser.add_parser("config")

    def parse(self):
        if self.is_first_time:
            pass
        args = self.parser.parse_args()
        if hasattr(args, "func"):
            args.func(args)
        else:
            self.parser.print_help()

    def download_model(self, args):
        CHOICES_STR = ["CheckPoint", "VAE", "Embeddings", "LoRA"]
        dw_type = que.select("ダウンロードするモデルのタイプ？", choices=CHOICES_STR, use_shortcuts=True).ask()
        dw_type = ModelType.cast(dw_type)

        que.select


class CLIConfig:
    def __init__(self, path):
        if isinstance(path, str):
            self.config_dir = Path(path)
        else:
            self.config_dir = path
        self.json_path = self.config_dir / "config.json"
        self.models_dir = self.config_dir / "models"

        self._validate_exists()

    def _validate_exists(self):
        if not self.config_dir.exists():
            raise FileNotFoundError("Config file does not exist.")
        if not self.config_dir.is_dir():
            raise ValueError("Selected path is not a directory.")
        if not self.json_path.exists():
            raise FileNotFoundError("config.json does not exist.")
        if not self.models_dir.exists():
            raise FileNotFoundError("Models directory is not found.")

    @property
    def config(self):
        if hasattr(self, "_config"):
            return self._config

        with self.json_path.open() as f:
            self._config = json.load(f)
        return self._config

    @property
    def model_list(self):
        if hasattr(self, "_models"):
            return self._models
        FILENAMES = ["CheckPoint.json", "Embeddings.json", "VAE.json", "LoRA.json"]
        result_dict = {
            ModelType.CHECKPOINT: None,
            ModelType.EMBEDDINGS: None,
            ModelType.VAE: None,
            ModelType.LORA: None,
        }

        for i in FILENAMES:
            with self.models_dir.joinpath(i).open() as f:
                result_dict[ModelType.cast(i.replace(".json", ""))] = json.load(f)
        self._models = result_dict
        return self._models

    def get_model_by_type(self, _type: ModelType):
        if hasattr(self, "_models"):
            return self._models[_type]
        return self.model_list[_type]


def get_config_dir() -> Path:
    p = Path(expanduser("~"))
    if (pl := platform.system()) == "Windows":
        p = p.joinpath(r"AppData\Local\StableDiffusionTools")
    elif pl == "Darwin":  # MacOS
        p = p.joinpath("Library/Preferences")
    else:
        p = p.joinpath(".config/StableDiffusionTools")
    return p


def get_diffusion_path() -> Path | None:
    path = Path.cwd()
    if path.name != "stable-diffusion-webui":
        p = list(path.glob("stable-diffusion-webui"))
        if not p:
            return None
        path = list(filter(lambda x: x.is_dir(), p))[0]
    return path


def initialize_configuration():
    path = get_config_dir()
    created = False
    if not path.exists():
        diff_p = get_diffusion_path()
        if diff_p is None:
            diff_p = que.path(
                "Stable Diffusionのパスを入力してください。",
                only_directories=True,
                validate=validators.PathDirValidator
            )
        create_config_file(path, Path(diff_p.ask()))
        created = True
    try:
        CLIConfig(path)
        return created
    except Exception:
        raise Exception("不正なConfig")


def create_config_file(config_dir: Path, diffusion_path: Path):
    if not config_dir.exists():
        config_dir.mkdir()
    config_json = config_dir.joinpath("config.json")
    TEMPLATE_JSON = {
        "diffusion_path": str(diffusion_path.absolute())
    }
    config_json.touch()
    config_json.write_text(json.dumps(TEMPLATE_JSON, indent=4), encoding="utf-8")

    models_dir = config_dir.joinpath("models")
    models_dir.mkdir()
    FILENAMES = ["CheckPoint.json", "Embeddings.json", "VAE.json", "LoRA.json"]
    for i in FILENAMES:
        p = models_dir.joinpath(i)
        p.touch()
        # TODO: build api server?
        # BASE_URL = "https://example.com/"
        # data = requests.get(BASE_URL + i)
        data = requests.get("https://dummyjson.com/quotes/100")
        p.write_text(json.dumps(data.json(), indent=4), encoding="utf-8")


if __name__ == "__main__":
    initialize_configuration()
    cli = MainCLI(get_config_dir(), True)
    cli.parse()
