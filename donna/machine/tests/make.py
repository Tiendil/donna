from typing import Any

from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.ids import SectionId
from donna.domain.internal_ids import ActionRequestId, TaskId, WorkUnitId
from donna.domain.python_path import PythonPath
from donna.machine.action_requests import ActionRequest
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionMeta
from donna.machine.state import MutableState
from donna.machine.tasks import Task, WorkUnit

ARTIFACT_ID = ArtifactId("@/workflows/test.donna.md")
PRIMARY_SECTION_ID = SectionId("workflow")
SECONDARY_SECTION_ID = SectionId("next")
PRIMITIVE_PATH = PythonPath("donna.machine.tests.test_primitives.sample_primitive")
PRIMARY_OPERATION_ID = ArtifactSectionId("@/workflows/test.donna.md:workflow")
SECONDARY_OPERATION_ID = ArtifactSectionId("@/workflows/test.donna.md:next")
TASK_ID = TaskId("T-1-b")
WORK_UNIT_ID = WorkUnitId("WU-2-c")
ACTION_REQUEST_ID = ActionRequestId("AR-3-d")


def artifact_section(
    *,
    id: SectionId = PRIMARY_SECTION_ID,
    artifact_id: ArtifactId = ARTIFACT_ID,
    kind: PythonPath = PRIMITIVE_PATH,
    title: str = "Workflow",
    description: str = "Workflow description",
    primary: bool = False,
    meta: ArtifactSectionMeta | None = None,
) -> ArtifactSection:
    return ArtifactSection(
        id=id,
        artifact_id=artifact_id,
        kind=kind,
        title=title,
        description=description,
        primary=primary,
        meta=meta or ArtifactSectionMeta(),
    )


def artifact(sections: list[ArtifactSection] | None = None) -> Artifact:
    if sections is None:
        sections = [artifact_section(primary=True)]

    return Artifact(id=ARTIFACT_ID, sections=sections)


def task(*, id: TaskId = TASK_ID, workflow_id: ArtifactSectionId = PRIMARY_OPERATION_ID) -> Task:
    return Task.build(id=id, workflow_id=workflow_id)


def work_unit(
    *,
    id: WorkUnitId = WORK_UNIT_ID,
    task_id: TaskId = TASK_ID,
    operation_id: ArtifactSectionId = PRIMARY_OPERATION_ID,
    context: dict[str, Any] | None = None,
) -> WorkUnit:
    return WorkUnit.build(id=id, task_id=task_id, operation_id=operation_id, context=context)


def action_request(
    *,
    id: ActionRequestId | None = ACTION_REQUEST_ID,
    title: str = "Action title",
    request: str = "Do the thing",
    operation_id: ArtifactSectionId = PRIMARY_OPERATION_ID,
) -> ActionRequest:
    return ActionRequest(id=id, title=title, request=request, operation_id=operation_id)


def mutable_state(
    *,
    tasks: list[Task] | None = None,
    work_units: list[WorkUnit] | None = None,
    action_requests: list[ActionRequest] | None = None,
    started: bool = True,
    last_id: int = 0,
) -> MutableState:
    return MutableState(
        tasks=tasks or [],
        work_units=work_units or [],
        action_requests=action_requests or [],
        started=started,
        last_id=last_id,
    )
