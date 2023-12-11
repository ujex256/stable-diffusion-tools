import argparse
from pathlib import Path
from pprint import pprint

import questionary as que

from . import cli_validator as val
from . import sd_image
from . import utils
from .config import CLIConfig, ModelType


class MainCLI:
    def __init__(self, config_dir: str | Path) -> None:
        self._config = CLIConfig(config_dir)
        self.parser = argparse.ArgumentParser("Stable Diffusion Tools")
        self.add_parser()

    def add_parser(self) -> None:
        self.actparser = self.parser.add_subparsers(title="action", description="動作", required=True)

        dw = self.actparser.add_parser("download", aliases=["dw", "dwm"], help="モデルをダウンロードします。")
        dw.set_defaults(func=self.download_model)

        conf_p = self.actparser.add_parser("config")
        conf_p.add_argument("--reset", action="store_true", help="Configをリセットします。")  # dummy arg
        conf_p.set_defaults(func=self.print_config)

        im_info = self.actparser.add_parser("img-info")
        im_info.add_argument(
            "filename", nargs="?", default=None, type=Path,
            help="ファイルのPathを指定してください。指定されなかった場合はプロンプトが表示されます。"
        )
        im_info.add_argument("--all-show", "--verbose", action="store_true", help="すべての要素を表示します。")
        im_info.set_defaults(func=self.show_img_info)

    def parse(self) -> None:
        args = self.parser.parse_args()
        if hasattr(args, "func"):
            args.func(args)
        else:
            self.parser.print_help()

    def download_model(self, args):
        CHOICES = ["CheckPoint", "VAE", "Embeddings", "LoRA"]
        dw_type = que.select("ダウンロードするモデルの種類を選択してください。", choices=CHOICES, use_shortcuts=True).ask()
        dw_type = ModelType.cast(dw_type)

        models = self._config.get_model_by_type(dw_type)
        name = que.select("モデルを選択してください。", choices=models.keys()).ask()
        # モデル以外ならそのままダウンロード
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
            img = Path(que.path("画像のパスを入力してください>> ", validate=val.ExistsValidator).ask())
        if not img.exists():
            raise FileNotFoundError(f"指定されたファイル {img}がありません。")
        meta = sd_image.SDImage(img)
        if meta is None:
            return "画像の解析に失敗しました。"

        show_attrs = ["Prompt", "Negative_prompt", "Sampler", "Seed", "Size", "Model", "VAE"]
        for i in meta.to_dict().items():
            if i[0] in show_attrs or args.all_show:
                print(f"{i[0]}: {i[1]}")
        print("Creation Date:", meta.time.ctime)

    def print_config(self, args) -> None:
        pprint(self._config.config)
