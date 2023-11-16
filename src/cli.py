import json
import argparse
import platform
import shutil
import sys
from pathlib import Path
from os import sep as pathsep
from os.path import expanduser
from enum import Enum
from pprint import pprint

import questionary as que
import requests

import utils
import exceptions as exc
import cli_validator as validators


# TODO: Config類を分ける
class ModelType(Enum):
    CHECKPOINT = "CheckPoint"
    CKPT = "CheckPoint"
    VAE = "VAE"
    EMBEDDINGS = "Embeddings"
    LORA = "LoRA"

    @classmethod
    def cast(cls, string: str) -> "ModelType":
        TYPES = [cls.CHECKPOINT, cls.VAE, cls.EMBEDDINGS, cls.LORA]
        TYPES_STR = list(map(lambda x: x.value.lower(), TYPES))
        if string.lower() not in TYPES_STR:
            return None
        return TYPES[TYPES_STR.index(string.lower())]

    def dir_name(self, diffusion_path: str | Path | None = None) -> Path | str:
        this = self.__class__
        DIRS = {
            this.CHECKPOINT: "/models/Stable-diffusion",
            this.CKPT: "/models/Stable-diffusion",
            this.VAE: "/models/VAE",
            this.EMBEDDINGS: "/embeddings",
            this.LORA: "/models/Lora"
        }
        if diffusion_path:
            if isinstance(diffusion_path, Path):
                return diffusion_path.joinpath(DIRS[self])
            elif isinstance(diffusion_path, str):
                rep_d = diffusion_path.replace("/", pathsep).rstrip(pathsep)
                return rep_d + DIRS[self].replace("/", pathsep)
        return DIRS[self]

    def __repr__(self) -> str:
        return super().__str__()


class MainCLI:
    def __init__(self, config_dir: str | Path, first_time: bool = True) -> None:
        self._config = CLIConfig(config_dir)
        self.parser = argparse.ArgumentParser("Stable Diffusion Tools")
        self.is_first_time = first_time
        self.add_parser()

    def add_parser(self) -> None:
        self.actparser = self.parser.add_subparsers(title="action", description="Do action", required=True)

        dw = self.actparser.add_parser("download", aliases=["dw", "dwm"], help="モデルをダウンロードします。")
        dw.set_defaults(func=self.download_model)
        confp = self.actparser.add_parser("config")
        confp.add_argument("--reset", help="Configをリセットします。")  # dummy arg
        confp.set_defaults(func=self.print_config)

    def parse(self) -> None:
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

        models = self._config.get_model_by_type(dw_type)
        name = que.select("モデルの名前を選択してください", choices=models.keys()).ask()

        que.print("! ", style="ansiblue", end="")
        que.print("ファイルサイズを取得中...", style="bold")
        print()
        weights = dict(filter(lambda x: bool(x[1]), models[name]["dw_url"].items()))  # not null
        select_text = map(
            lambda x: f"{x[0]} ({utils.generate_size_str(x[1]['url'])})",
            weights.items()
        )
        selected_weight = que.select("サイズを選択してください。", choices=list(select_text)).ask()

        sd: dict = weights[utils.remove_filesize_string(selected_weight)]
        target_dir = Path(dw_type.dir_name(self._config.sd_path))
        utils.download_model(sd["url"], target_dir, sd.get("sha256"))

    def print_config(self, args) -> None:
        pprint(self._config.config)


class CLIConfig:
    def __init__(self, path) -> None:
        if isinstance(path, str):
            self.config_dir = Path(path)
        else:
            self.config_dir = path
        self.json_path = self.config_dir / "config.json"
        self.models_dir = self.config_dir / "models"

        self._validate_exists()

    def _validate_exists(self) -> bool:
        if not self.config_dir.exists():
            raise FileNotFoundError("Config file does not exist.")
        if not self.config_dir.is_dir():
            raise ValueError("Selected path is not a directory.")
        if not self.json_path.exists():
            raise FileNotFoundError("config.json does not exist.")
        if not self.models_dir.exists():
            raise FileNotFoundError("Models directory is not found.")

    @property
    def config(self) -> dict:
        if hasattr(self, "_config"):
            return self._config

        with self.json_path.open() as f:
            self._config = json.load(f)
        return self._config

    @property
    def model_list(self) -> dict:
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

    def get_model_by_type(self, _type: ModelType) -> dict:
        if hasattr(self, "_models"):
            return self._models[_type]
        return self.model_list[_type]

    @property
    def sd_path(self):
        return self.config["diffusion_path"]


def get_config_dir() -> Path:
    p = Path(expanduser("~"))
    if (pl := platform.system()) == "Windows":
        p = p.joinpath(r"AppData\Local\StableDiffusionTools")
    elif pl == "Darwin":  # MacOS
        p = p.joinpath("Library/Preferences/StableDiffusionTools")
    else:
        p = p.joinpath(".config/StableDiffusionTools")
    return p


def reset_config(path: Path | str) -> None:
    shutil.rmtree(str(path.absolute()) if isinstance(path, Path) else path)


def get_diffusion_path() -> Path | None:
    path = Path.cwd()
    if path.name != "stable-diffusion-webui":
        p = list(path.glob("stable-diffusion-webui"))
        if not p:
            return None
        path = list(filter(lambda x: x.is_dir(), p))[0]
    return path


def initialize_configuration() -> bool:
    path = get_config_dir()
    created = False

    if sys.argv[1:3] == ["config", "--reset"]:
        reset_config(path)
        print("Delete Completed.")
        sys.exit(0)
    if not path.exists():
        diff_p = get_diffusion_path()
        if diff_p:
            a = que.confirm(
                f"Stable Diffusionのパスを検出しました！これでよろしいですか？\n{diff_p.absolute()}"
            )
            if not a.ask():
                diff_p = None
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
        raise exc.InvalidConfig(path, "Invalid config file. Please reset your configuration.")


def create_config_file(config_dir: Path, diffusion_path: Path) -> None:
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

        BASE_URL = "https://modelsjson-1-t1657038.deta.app/json/"
        data = requests.get(BASE_URL + i)
        if not data.ok:
            raise exc.ResourceGetFailed(f"Request Failed. Please try again. (url: {data.url} )")
        p.write_text(json.dumps(data.json(), indent=4), encoding="utf-8")


if __name__ == "__main__":
    initialize_configuration()
    cli = MainCLI(get_config_dir(), True)
    cli.parse()
