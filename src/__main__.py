from .cli import MainCLI
from .config import initialize_configuration, get_config_dir

from traceback import format_exception_only


def main():
    try:
        initialize_configuration()
        cli = MainCLI(get_config_dir())
        cli.parse()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
    except Exception as e:
        print("エラーが発生しました。")
        print(format_exception_only(type(e), e)[0][:-1])
