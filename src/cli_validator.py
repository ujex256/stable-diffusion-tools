from prompt_toolkit.document import Document
from questionary import Validator, ValidationError
from os.path import isdir, exists


class PathDirValidator(Validator):
    def validate(self, document: Document) -> None:
        if not isdir(document.text):
            raise ValidationError(
                message="Stable Diffusion path is must be a directory.",
                cursor_position=len(document.text)
            )


class ExistsValidator(Validator):
    def validate(self, document: Document) -> None:
        if not exists(document.text):
            raise ValidationError(
                message="File does not exist",
                cursor_position=len(document.text)
            )
