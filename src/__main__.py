from .cli import MainCLI
from .config import initialize_configuration, get_config_dir


def main():
    try:
        initialize_configuration()
        cli = MainCLI(get_config_dir())
        cli.parse()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
