import re
from typing import TYPE_CHECKING, Iterator, Literal, cast

from donna.domain.ids import FullArtifactId, FullArtifactLocalId, OperationKindId
from donna.machine.action_requests import ActionRequest
from donna.machine.operations import OperationConfig, OperationKind, FsmMode, OperationMeta
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource
from donna.machine.artifacts import ArtifactSection, ArtifactSectionKindId

if TYPE_CHECKING:
    from donna.machine.changes import Change


##########################
# Request Action Operation
##########################


def extract_transitions(text: str) -> set[FullArtifactLocalId]:
    """Extracts all transitions from the text of action request.

    Transition is specified as render of `goto` command in the format:
    ```
    $$donna todo <full_artifact_local_id> donna$$
    ```
    """
    pattern = r"\$\$donna\s+goto\s+([a-zA-Z0-9_\-.:/]+)\s+donna\$\$"
    matches = re.findall(pattern, text)

    transitions: set[FullArtifactLocalId] = set()

    for match in matches:
        transitions.add(FullArtifactLocalId.parse(match))

    return transitions


class RequestActionConfig(OperationConfig):
    pass


class RequestActionKind(OperationKind):

    def construct(  # type: ignore[override]
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
            description=section.as_original_markdown(),
            meta=OperationMeta(fsm_mode=config.fsm_mode,
                               allowed_transtions=extract_transitions(section.as_analysis_markdown())),
        )

    def execute(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddActionRequest

        context: dict[str, object] = {
            "scheme": operation,
            "task": task,
            "work_unit": unit,
        }

        request_text = operation.description.format(**context)

        request = ActionRequest.build(request_text, operation.id)

        yield ChangeAddActionRequest(action_request=request)


request_action_kind = RequestActionKind(
    id=ArtifactSectionKindId("request_action"),
    title="Request Action",
)


##################
# Finish Operation
##################


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflowKind(OperationKind):
    def execute(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        yield ChangeFinishTask(task_id=task.id)

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> ArtifactSection:
        config = FinishWorkflowConfig.parse_obj(section.merged_configs())

        title = section.title or ""

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=self.id,
            title=title,
            description=section.as_original_markdown(),
            meta=OperationMeta(fsm_mode=config.fsm_mode,
                               allowed_transtions=set()))


finish_workflow_kind = FinishWorkflowKind(
    id=ArtifactSectionKindId("finish_workflow"),
    title="Finish Workflow",
)
