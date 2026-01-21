import re
from typing import TYPE_CHECKING, Iterator, Literal

import pydantic

from donna.domain.ids import ArtifactId, ArtifactLocalId, FullArtifactId, FullArtifactLocalId, WorldId
from donna.machine.action_requests import ActionRequest
from donna.machine.artifacts import ArtifactSection, ArtifactSectionTextKind, PythonModuleSectionKind
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


OPERATIONS_WORLD_ID = WorldId("donna")
OPERATIONS_ARTIFACT_ID = ArtifactId("operations")


def operations_section_id(local_id: str) -> FullArtifactLocalId:
    return FullArtifactLocalId((OPERATIONS_WORLD_ID, OPERATIONS_ARTIFACT_ID, ArtifactLocalId(local_id)))


text_section_kind = ArtifactSectionTextKind(
    id=operations_section_id("text"),
    title="Text Section",
)


python_module_section_kind = PythonModuleSectionKind(
    id=operations_section_id("python_module"),
    title="Python module attribute",
)


##########################
# Request Action Operation
##########################


def extract_transitions(text: str) -> set[FullArtifactLocalId]:
    """Extracts all transitions from the text of action request.

    Transition is specified as render of `goto` directive in the format:
    ```
    $$donna goto <full_artifact_local_id> donna$$
    ```
    """
    pattern = r"\$\$donna\s+goto\s+([a-zA-Z0-9_\-.:/]+)\s+donna\$\$"
    matches = re.findall(pattern, text)

    transitions: set[FullArtifactLocalId] = set()

    for match in matches:
        transitions.add(FullArtifactLocalId.parse(match))

    return transitions


class RequestActionConfig(OperationConfig):

    @pydantic.field_validator("fsm_mode", mode="after")
    @classmethod
    def validate_fsm_mode(cls, v: FsmMode) -> FsmMode:
        if v == FsmMode.final:
            raise ValueError("RequestAction operation cannot have 'final' fsm_mode")

        return v


class RequestActionKind(OperationKind):

    def construct_section(
        self,
        artifact_id: FullArtifactId,
        section: SectionSource,
    ) -> "ArtifactSection":
        config = RequestActionConfig.parse_obj(section.merged_configs())

        title = section.title or ""

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=self.id,
            title=title,
            description=section.as_original_markdown(with_title=False),
            meta=OperationMeta(
                fsm_mode=config.fsm_mode,
                allowed_transtions=extract_transitions(section.as_analysis_markdown(with_title=True)),
            ),
        )

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddActionRequest

        context: dict[str, object] = {
            "scheme": operation,
            "task": task,
            "work_unit": unit,
        }

        request_text = operation.description.format(**context)

        assert operation.id is not None

        request = ActionRequest.build(request_text, operation.id)

        yield ChangeAddActionRequest(action_request=request)


request_action_kind = RequestActionKind(
    id=operations_section_id("request_action"),
    title="Request Action",
)


##################
# Finish Operation
##################


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflowKind(OperationKind):
    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        yield ChangeFinishTask(task_id=task.id)

    def construct_section(self, artifact_id: FullArtifactId, section: SectionSource) -> ArtifactSection:
        config = FinishWorkflowConfig.parse_obj(section.merged_configs())

        title = section.title or ""

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=self.id,
            title=title,
            description=section.as_original_markdown(with_title=False),
            meta=OperationMeta(fsm_mode=config.fsm_mode, allowed_transtions=set()),
        )


finish_workflow_kind = FinishWorkflowKind(
    id=operations_section_id("finish_workflow"),
    title="Finish Workflow",
)
