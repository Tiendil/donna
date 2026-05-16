import pathlib
from typing import Sequence

from donna.domain.constants import ARTIFACT_ID_PREFIX
from donna.domain.id_paths import IdPath, NormalizedRawIdPath
from donna.domain.ids import SectionId, _is_artifact_slug_part


class ArtifactId(IdPath):
    __slots__ = ()
    prefix = ARTIFACT_ID_PREFIX
    delimiter = "/"
    validate_json = True

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        if not parts:
            return False

        if not all(_is_artifact_slug_part(part) for part in parts):
            return False

        return bool(pathlib.PurePosixPath(parts[-1]).suffix)

    def to_full_local(self, local_id: SectionId) -> "ArtifactSectionId":
        return ArtifactSectionId(NormalizedRawIdPath(f"{self.raw_value}:{local_id}"))


class ArtifactSectionId(IdPath):
    __slots__ = ()
    prefix = ARTIFACT_ID_PREFIX
    delimiter = ":"
    min_parts = 2
    validate_json = True

    @classmethod
    def _validate_parts(cls, parts: Sequence[str]) -> bool:
        if len(parts) < cls.min_parts:
            return False

        return ArtifactId.validate(cls.delimiter.join(parts[:-1])) and SectionId.validate(parts[-1])

    @property
    def artifact_id(self) -> ArtifactId:
        return ArtifactId(NormalizedRawIdPath(self.delimiter.join(self.parts[:-1])))

    @property
    def local_id(self) -> SectionId:
        return SectionId(self.parts[-1])
