from typing import Sequence

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.id_paths import IdPath, IdPathPattern, _invalid_format
from donna.domain.ids import SectionId, _is_artifact_slug_part


class ArtifactId(IdPath):
    __slots__ = ()
    delimiter = ":"
    validate_json = True

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        return all(_is_artifact_slug_part(part) for part in parts)

    def to_full_local(self, local_id: SectionId) -> "ArtifactSectionId":
        return ArtifactSectionId(f"{self}:{local_id}")

    @classmethod
    def parse(cls, text: str) -> Result["ArtifactId", ErrorsList]:
        if not isinstance(text, str) or not text:
            return _invalid_format(cls.__name__, text)

        if not cls.delimiter:
            return _invalid_format(cls.__name__, text)

        if not cls.validate(text):
            return _invalid_format(cls.__name__, text)

        return Ok(cls(text))


class ArtifactIdPattern(IdPathPattern["ArtifactId"]):
    __slots__ = ()
    id_class = ArtifactId

    @classmethod
    def _validate_pattern_part(cls, part: str) -> bool:
        if part in {"*", "**"}:
            return True

        return _is_artifact_slug_part(part)


class _ColonPath(IdPath):
    __slots__ = ()
    delimiter = ":"


class ArtifactSectionId(_ColonPath):
    __slots__ = ()
    min_parts = 2
    validate_json = True

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        if len(parts) < cls.min_parts:
            return False

        return ArtifactId.validate(cls.delimiter.join(parts[:-1])) and SectionId.validate(parts[-1])

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(self.delimiter.join(self.parts[:-1]))

    @property
    def full_artifact_id(self) -> ArtifactId:
        return self.artifact_id

    @property
    def local_id(self) -> SectionId:
        return SectionId(self.parts[-1])

    @property
    def short(self) -> str:
        parts = str(self).split(self.delimiter)
        new_parts = [part[0] for part in parts[:-2]] + parts[-2:]
        return self.delimiter.join(new_parts)

    @classmethod
    def parse(cls, text: str) -> Result["ArtifactSectionId", ErrorsList]:  # noqa: CCR001
        if not isinstance(text, str) or not text:
            return _invalid_format(f"{cls.__name__} format", text)

        if not cls.delimiter:
            return _invalid_format(f"{cls.__name__} format", text)

        try:
            artifact_part, local_part = text.rsplit(cls.delimiter, maxsplit=1)
        except ValueError:
            return _invalid_format(f"{cls.__name__} format", text)

        full_artifact_id_result = ArtifactId.parse(artifact_part)
        errors = full_artifact_id_result.err()
        if errors is not None:
            return Err(errors)

        artifact_id = full_artifact_id_result.ok()
        if artifact_id is None:
            return _invalid_format(f"{cls.__name__} format", text)

        local_id_result = SectionId.parse(local_part)
        local_errors = local_id_result.err()
        if local_errors is not None:
            return Err(local_errors)

        local_id = local_id_result.ok()
        if local_id is None:
            return _invalid_format(f"{cls.__name__} format", text)

        return Ok(cls(f"{artifact_id}{cls.delimiter}{local_id}"))
