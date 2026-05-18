import pathlib

from donna.domain.artifact_ids import ArtifactId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.paths import ProjectConfigPath, ProjectRootPath
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import ArtifactSectionConfig
from donna.workspaces import markdown
from donna.workspaces.config import Config, Workspace
from donna.workspaces.markdown import CodeSource, SectionLevel, SectionSource

ARTIFACT_ID = ArtifactId("@/workflows/test.donna.md")
TEXT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.text.Text"))


def workspace(root: pathlib.Path, config: Config | None = None) -> Workspace:
    return Workspace(
        root=ProjectRootPath(root),
        config_path=ProjectConfigPath(root / "donna.toml"),
        config=config or Config(),
    )


def section_source(
    *,
    level: SectionLevel = SectionLevel.h2,
    title: str | None = "Section",
    configs: list[CodeSource] | None = None,
) -> SectionSource:
    return SectionSource(
        level=level,
        title=title,
        configs=configs or [],
        original_tokens=[],
        analysis_tokens=[],
    )


def code_source(format: str = "toml", content: str = "", **properties: str | bool) -> CodeSource:
    return CodeSource(format=format, content=content, properties=properties)


def section_source_from_markdown(text: str, section_index: int = 0) -> SectionSource:
    source = markdown.parse(text, artifact_id=ARTIFACT_ID).unwrap()[section_index]
    source.analysis_tokens.extend(source.original_tokens)
    return source


def section_config(
    *,
    id: SectionId = SectionId("section"),
    kind: PythonPath = TEXT_KIND,
) -> ArtifactSectionConfig:
    return ArtifactSectionConfig(id=id, kind=kind)
