from pathlib import Path as _Path


class InvalidConfig(Exception):
    def __init__(self, invalid_path: str | _Path, *args: object) -> None:
        super().__init__(*args)
        if isinstance(invalid_path, _Path):
            self.path = str(invalid_path.absolute())
        else:
            self.path = invalid_path


class ResourceGetFailed(Exception):
    pass
