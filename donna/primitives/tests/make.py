from typing import Any, cast

from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionMeta
from donna.machine.tasks import Task, WorkUnit
from donna.protocol.cells import Cell
from donna.protocol.journal import JournalRecord
from donna.workspaces import markdown
from donna.workspaces.markdown import CodeSource, SectionLevel, SectionSource

ARTIFACT_ID = ArtifactId("@/workflows/test.donna.md")
WORKFLOW_SECTION_ID = SectionId("workflow")
START_SECTION_ID = SectionId("start")
NEXT_SECTION_ID = SectionId("next")
DONE_SECTION_ID = SectionId("done")
OTHER_SECTION_ID = SectionId("other")
WORKFLOW_OPERATION_ID = ArtifactSectionId("@/workflows/test.donna.md:workflow")
START_OPERATION_ID = ArtifactSectionId("@/workflows/test.donna.md:start")
TASK_ID = TaskId("T-1-b")
WORK_UNIT_ID = WorkUnitId("WU-2-c")

WORKFLOW_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.artifacts.workflow.Workflow"))
TEXT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.text.Text"))
REQUEST_ACTION_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.request_action.RequestAction"))
OUTPUT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.output.Output"))
RUN_SCRIPT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.run_script.RunScript"))
FINISH_WORKFLOW_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.finish_workflow.FinishWorkflow"))


def artifact_section(
    *,
    id: SectionId = START_SECTION_ID,
    kind: PythonPath = TEXT_KIND,
    title: str = "Step",
    description: str = "Step description",
    primary: bool = False,
    meta: ArtifactSectionMeta | None = None,
) -> ArtifactSection:
    return ArtifactSection(
        id=id,
        artifact_id=ARTIFACT_ID,
        kind=kind,
        title=title,
        description=description,
        primary=primary,
        meta=meta or ArtifactSectionMeta(),
    )


def artifact(sections: list[ArtifactSection]) -> Artifact:
    return Artifact(id=ARTIFACT_ID, sections=sections)


def task(*, id: TaskId = TASK_ID, workflow_id: ArtifactSectionId = WORKFLOW_OPERATION_ID) -> Task:
    return Task.build(id=id, workflow_id=workflow_id)


def work_unit(
    *,
    id: WorkUnitId = WORK_UNIT_ID,
    task_id: TaskId = TASK_ID,
    operation_id: ArtifactSectionId = START_OPERATION_ID,
    context: dict[str, Any] | None = None,
) -> WorkUnit:
    return WorkUnit.build(id=id, task_id=task_id, operation_id=operation_id, context=context)


def code_source(format: str = "toml", content: str = "", **properties: str | bool) -> CodeSource:
    return CodeSource(format=format, content=content, properties=properties)


def section_source(
    *,
    level: SectionLevel = SectionLevel.h2,
    title: str | None = "Step",
    configs: list[CodeSource] | None = None,
) -> SectionSource:
    return SectionSource(
        level=level,
        title=title,
        configs=configs or [],
        original_tokens=[],
        analysis_tokens=[],
    )


def section_source_from_markdown(text: str, section_index: int = 0) -> SectionSource:
    source = markdown.parse(text, artifact_id=ARTIFACT_ID).unwrap()[section_index]
    source.analysis_tokens.extend(source.original_tokens)
    return source


def template_context(**values: Any) -> Context:
    return cast(Context, values)


class FakeOutputEmitter:
    def __init__(self) -> None:
        self.cells: list[Cell] = []
        self.journal_records: list[JournalRecord] = []

    def emit_cell(self, cell: Cell) -> None:
        self.cells.append(cell)

    def emit_journal(self, record: JournalRecord) -> None:
        self.journal_records.append(record)


class FakeJournal:
    def __init__(self) -> None:
        self.messages: list[tuple[str | None, str]] = []

    def add(self, message: str, actor_id: str | None = None) -> Result[BaseEntity, ErrorsList]:
        self.messages.append((actor_id, message))
        return Ok(BaseEntity())


class FakeRuntimeContext:
    def __init__(self) -> None:
        self.output = FakeOutputEmitter()
        self.journal = FakeJournal()
