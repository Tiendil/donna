from types import ModuleType
from typing import Literal

from donna.domain.ids import FullArtifactId, PythonImportPath
from donna.machine.artifacts import Artifact, ArtifactSection
from donna.world.sources.base import SourceConfig


class Config(SourceConfig):
    kind: Literal["python"] = "python"


def construct_artifact_from_bytes(full_id: FullArtifactId, content: bytes) -> Artifact:
    module = _load_module_from_bytes(
        content,
        module_name=f"donna.world.sources.python.{full_id.world_id}.{full_id.artifact_id}",
    )
    return construct_artifact_from_module(module, full_id)


def construct_artifact_from_module(module: ModuleType, full_id: FullArtifactId) -> Artifact:  # noqa: CCR001
    sections: list[ArtifactSection] = []

    for name, value in sorted(module.__dict__.items()):
        if not name.isidentifier():
            continue

        if name.startswith("_"):
            continue

        if isinstance(value, ArtifactSection):
            sections.append(value)

    primary_sections = [section for section in sections if section.primary]
    if len(primary_sections) != 1:
        raise NotImplementedError(
            f"Module `{module.__name__}` must define exactly one primary section, found {len(primary_sections)}."
        )

    primary_section = primary_sections[0]

    if isinstance(primary_section.kind, str):
        primary_kind = PythonImportPath.parse(primary_section.kind)
        primary_section = primary_section.replace(kind=primary_kind)
        sections = [primary_section if section is primary_sections[0] else section for section in sections]

    expected_kind_id = PythonImportPath.parse("donna.lib.python_artifact")
    if primary_section.kind != expected_kind_id:
        raise NotImplementedError(
            f"Primary section kind mismatch: module uses '{primary_section.kind}', but expected '{expected_kind_id}'."
        )

    return Artifact(
        id=full_id,
        sections=sections,
    )


# TODO: potentially dangerous, do we really need to use exec to verify module contents?
#       - ideally — yes
#       - practically — maybe it is enough to check syntax only without executing it
def _load_module_from_bytes(content: bytes, module_name: str) -> ModuleType:
    module = ModuleType(module_name)
    exec(compile(content, module_name, "exec"), module.__dict__)  # noqa: S102
    return module
