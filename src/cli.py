import argparse
from pathlib import Path
from pprint import pprint

import questionary as que

import cli_validator as validators
import sd_image
import utils
from config import CLIConfig, ModelType, get_config_dir, initialize_configuration


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

        iinfo = self.actparser.add_parser("img-info")
        iinfo.add_argument("filename", nargs="?", default=None, type=Path)
        iinfo.add_argument("--all-show", "--verbose", action="store_true")
        iinfo.set_defaults(func=self.show_img_info)

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
        dw_type = que.select("ダウンロードするモデルの種類を選択してください。", choices=CHOICES_STR, use_shortcuts=True).ask()
        dw_type = ModelType.cast(dw_type)

        models = self._config.get_model_by_type(dw_type)
        name = que.select("モデルを選択してください。", choices=models.keys()).ask()
        if dw_type is not ModelType.CHECKPOINT:
            target_dir = Path(dw_type.dir_name(self._config.sd_path))
            sha256 = models[name].get("sha256")
            utils.download_model(models[name]["dw_url"], target_dir, sha256)
            return

        que.print("! ", style="ansiblue", end="")
        que.print("ファイルサイズを取得中...", style="bold")
        print()
        weights = dict(filter(lambda x: bool(x[1]), models[name]["dw_url"].items()))  # not null
        select_text = map(
            lambda x: f"{x[0]} ({utils.generate_size_str(x[1]['url'])})",
            weights.items()
        )
        selected_weight = que.select("モデルのサイズを選択してください。", choices=list(select_text)).ask()

        sd: dict = weights[utils.remove_filesize_string(selected_weight)]
        target_dir = Path(dw_type.dir_name(self._config.sd_path))
        utils.download_model(sd["url"], target_dir, sd.get("sha256"))

    def show_img_info(self, args):
        if not args.filename:
            imgp = Path(que.path("画像のパスを入力してください>> ", validate=validators.ExistsValidator).ask())
        if not imgp.exists():
            raise FileNotFoundError(f"指定されたファイル {imgp}がありません。")
        meta = sd_image.SDImage(imgp)
        show_attrs = ["Prompt", "Negative_prompt", "Sampler", "Seed", "Size", "Model", "VAE"]
        for i in meta.to_dict().items():
            if i[0] in show_attrs or args.all_show:
                print(f"{i[0]}: {i[1]}")

    def print_config(self, args) -> None:
        pprint(self._config.config)


if __name__ == "__main__":
    initialize_configuration()
    cli = MainCLI(get_config_dir(), True)
    cli.parse()
