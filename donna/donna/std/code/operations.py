import re
from typing import TYPE_CHECKING, Iterator, Literal, cast

from donna.domain.ids import FullArtifactId, FullArtifactLocalId, OperationKindId
from donna.machine.action_requests import ActionRequest
from donna.machine.operations import Operation, OperationConfig, OperationKind, OperationMode
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource

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
    ) -> "RequestAction":
        config = RequestActionConfig.parse_obj(section.merged_configs())

        title = section.title or ""

        return RequestAction(
            config=config,
            title=title,
            artifact_id=artifact_id,
            allowed_transtions=extract_transitions(section.as_analysis_markdown()),
            request_template=section.as_original_markdown(),
        )

    def construct_context(self, task: Task, operation: "RequestAction") -> dict[str, object]:
        context: dict[str, object] = {}

        for method_name in dir(operation):
            if not method_name.startswith("context_"):
                continue

            name = method_name[len("context_") :]
            value = getattr(operation, method_name)(task)

            if value is None:
                continue

            context[name] = value

        context["scheme"] = operation

        return context

    def execute(self, task: Task, unit: WorkUnit, operation: Operation) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddActionRequest

        operation = cast(RequestAction, operation)
        context = self.construct_context(task, operation)

        request_text = operation.request_template.format(**context)

        request = ActionRequest.build(request_text, operation.full_id)

        yield ChangeAddActionRequest(request)


class RequestAction(Operation):
    request_template: str


request_action_kind = RequestActionKind(
    id=OperationKindId("request_action"),
    title="Request Action",
)


##################
# Finish Operation
##################


class FinishWorkflowConfig(OperationConfig):
    mode: Literal[OperationMode.final] = OperationMode.final


class FinishWorkflowKind(OperationKind):
    def execute(self, task: Task, unit: WorkUnit, operation: Operation) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        yield ChangeFinishTask(task.id)

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> "Operation":  # type: ignore[override]
        config = FinishWorkflowConfig.parse_obj(section.merged_configs())

        title = section.title or ""

        return Operation(config=config, title=title, artifact_id=artifact_id, allowed_transtions=set())


finish_workflow_kind = FinishWorkflowKind(
    id=OperationKindId("finish_workflow"),
    title="Finish Workflow",
)
