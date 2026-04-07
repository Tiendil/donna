import pathlib
from typing import Sequence

from donna.domain.id_paths import (
    IdPath,
    IdPathPattern,
    IdPathSegmentLiteralMatcher,
    IdPathSegmentMatcher,
    IdPathSegmentRecursiveMatcher,
    IdPathSegmentSingleMatcher,
    NormalizedRawIdPath,
)
from donna.domain.ids import SectionId, _is_artifact_slug_part

ARTIFACT_ID_PREFIX = "@/"
_ARTIFACT_PATTERN_EXTRA_CHARACTERS = set("*?[]")


def _is_artifact_pattern_part(part: str) -> bool:
    if not part:
        return False

    if part == "**":
        return True

    allowed_characters = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    allowed_characters.update(_ARTIFACT_PATTERN_EXTRA_CHARACTERS)

    if any(character not in allowed_characters for character in part):
        return False

    return any(character not in ".-" for character in part)


def normalize_path(  # noqa: CCR001
    text: str,
    *,
    relative_to: "ArtifactId | None" = None,
    allow_wildcards: bool,
) -> NormalizedRawIdPath | None:
    if not isinstance(text, str) or not text:
        return None

    if text.startswith("/"):
        return None

    if text.startswith(ARTIFACT_ID_PREFIX):
        raw = text.removeprefix(ARTIFACT_ID_PREFIX)
        normalized_parts: list[str] = []
    else:
        raw = text
        normalized_parts = list(relative_to.parts[:-1]) if relative_to is not None else []

    if not raw:
        return None

    for part in raw.split("/"):
        if part == "":
            return None

        if part == ".":
            continue

        if part == "..":
            if not normalized_parts:
                return None
            normalized_parts.pop()
            continue

        if allow_wildcards:
            if not _is_artifact_pattern_part(part):
                return None
        elif not _is_artifact_slug_part(part):
            return None

        normalized_parts.append(part)

    if not normalized_parts:
        return None

    last_part = normalized_parts[-1]
    if not allow_wildcards or last_part not in {"*", "**"}:
        if not pathlib.PurePosixPath(last_part).suffix:
            return None

    return NormalizedRawIdPath("/".join(normalized_parts))


def normalize_artifact_section_id(text: str, *, relative_to: "ArtifactId | None" = None) -> NormalizedRawIdPath | None:
    if not isinstance(text, str) or not text:
        return None

    try:
        artifact_part, local_part = text.rsplit(ArtifactSectionId.delimiter, maxsplit=1)
    except ValueError:
        return None

    normalized_artifact_id = normalize_path(artifact_part, relative_to=relative_to, allow_wildcards=False)
    if normalized_artifact_id is None or not SectionId.validate(local_part):
        return None

    return NormalizedRawIdPath(f"{normalized_artifact_id}{ArtifactSectionId.delimiter}{local_part}")


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


class ArtifactIdPattern(IdPathPattern["ArtifactId"]):
    __slots__ = ()
    id_class = ArtifactId

    def __str__(self) -> str:
        rendered = self.id_class.delimiter.join(str(part) for part in self)
        if self and not isinstance(self[0], IdPathSegmentLiteralMatcher):
            return rendered

        return f"{self.id_class.prefix}{rendered}"

    @classmethod
    def _parse_pattern_part(cls, part: str) -> IdPathSegmentMatcher | None:
        if part == "**":
            return IdPathSegmentRecursiveMatcher(part)

        if not _is_artifact_pattern_part(part):
            return None

        if any(char in part for char in _ARTIFACT_PATTERN_EXTRA_CHARACTERS):
            return IdPathSegmentSingleMatcher(part)

        return IdPathSegmentLiteralMatcher(part)


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
