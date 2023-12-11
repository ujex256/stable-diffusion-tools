import json
import platform
import shutil
import sys
from enum import Enum
from os import sep as pathsep
from pathlib import Path

import questionary as que
import requests

from . import cli_validator as val
from . import exceptions as exc


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
        """そのモデルをどこに配置するか返します

        Args:
            diffusion_path (str | Path | None, optional): webuiがあるディレクトリのPath

        Returns:
            Path | str: 入力された型で返します。Noneの場合はstrです
        """
        DIRS = {
            self.CHECKPOINT: "/models/Stable-diffusion",
            self.CKPT: "/models/Stable-diffusion",
            self.VAE: "/models/VAE",
            self.EMBEDDINGS: "/embeddings",
            self.LORA: "/models/Lora"
        }
        if diffusion_path:
            if isinstance(diffusion_path, Path):
                return diffusion_path.joinpath(DIRS[self])
            elif isinstance(diffusion_path, str):
                rep_d = diffusion_path.replace("/", pathsep).replace("\\", pathsep).rstrip(pathsep)
                return rep_d + DIRS[self].replace("/", pathsep)
        return DIRS[self]

    def __repr__(self) -> str:
        return super().__str__()


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
        """入力されたタイプのモデル一覧を返します

        Args:
            _type (ModelType): モデルのタイプ

        Returns:
            dict: モデル一覧
        """
        if hasattr(self, "_models"):
            return self._models[_type]
        return self.model_list[_type]

    @property
    def sd_path(self):
        return self.config["diffusion_path"]


def get_config_dir() -> Path:
    p = Path.home()
    if (pl := platform.system()) == "Windows":
        p = p.joinpath(r"AppData\Roaming\sdtools")
    elif pl == "Darwin":  # MacOS
        p = p.joinpath("Library/Preferences/sdtools")
    else:
        p = p.joinpath(".config/sdtools")
    return p


def reset_config(path: Path | str) -> None:
    shutil.rmtree(str(path.resolve()) if isinstance(path, Path) else path)


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
                validate=val.PathDirValidator
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
        "diffusion_path": str(diffusion_path.resolve())
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
