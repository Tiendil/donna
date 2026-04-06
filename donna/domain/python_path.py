from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.id_paths import IdPath, _invalid_format


class PythonPath(IdPath):
    __slots__ = ()
    delimiter = "."

    @classmethod
    def parse(cls, text: str) -> Result["PythonPath", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))
