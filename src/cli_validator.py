from prompt_toolkit.document import Document
from questionary import Validator, ValidationError
from os.path import isdir


class PathDirValidator(Validator):
    def validate(self, document: Document) -> None:
        if not isdir(document.text):
            raise ValidationError(
                message="Stable Diffusion path is must be a directory.",
                cursor_position=len(document.text)
            )
