import datetime
import pathlib

from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.domain.paths import ProjectConfigPath, ProjectRootPath
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import ArtifactSectionConfig
from donna.protocol.journal import JournalRecord
from donna.workspaces.config import Config, Workspace
from donna.workspaces.markdown import CodeSource, SectionLevel, SectionSource

ARTIFACT_ID = ArtifactId("@/workflows/test.donna.md")
OPERATION_ID = ArtifactSectionId("@/workflows/test.donna.md:primary")
TEXT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.text.Text"))


def workspace(root: pathlib.Path, config: Config | None = None) -> Workspace:
    return Workspace(
        root=ProjectRootPath(root),
        config_path=ProjectConfigPath(root / "donna.toml"),
        config=config or Config(),
    )


def journal_record(
    *,
    actor_id: str | None = "agent",
    current_task_id: TaskId | None = TaskId("T-1-b"),
    current_work_unit_id: WorkUnitId | None = WorkUnitId("WU-2-c"),
    current_operation_id: ArtifactSectionId | None = OPERATION_ID,
) -> JournalRecord:
    return JournalRecord(
        timestamp=datetime.datetime(2026, 5, 18, 10, 30, tzinfo=datetime.UTC),
        actor_id=actor_id,
        message="message",
        current_task_id=current_task_id,
        current_work_unit_id=current_work_unit_id,
        current_operation_id=current_operation_id,
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


def code_source(format: str, content: str, **properties: str | bool) -> CodeSource:
    return CodeSource(format=format, content=content, properties=properties)


def section_config(
    *,
    id: SectionId = SectionId("section"),
    kind: PythonPath = TEXT_KIND,
) -> ArtifactSectionConfig:
    return ArtifactSectionConfig(id=id, kind=kind)
