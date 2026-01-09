from typing import TYPE_CHECKING, Iterator, cast

from donna.domain.ids import FullArtifactId
from donna.machine.action_requests import ActionRequest
from donna.machine.operations import Operation, OperationKind
from donna.machine.tasks import Task, TaskState, WorkUnit
from donna.world.markdown import SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


##########################
# Request Action Operation
##########################


class RequestActionKind(OperationKind):

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> "RequestAction":  # type: ignore[override]
        data = section.merged_configs()

        if "title" not in data:
            data["title"] = section.title or "Untitled Request Action"

        if "request_template" not in data:
            data["request_template"] = section.as_markdown()

        if "artifact_id" in data:
            raise NotImplementedError("artifact_id should not be set in RequestActionKind.construct")

        data["artifact_id"] = str(artifact_id)

        return cast(RequestAction, self.operation(**data))

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


request_action_kind = RequestActionKind(id="request_action", title="Request Action", operation=RequestAction)


##################
# Finish Operation
##################


class FinishWorkflowKind(OperationKind):
    def execute(self, task: Task, unit: WorkUnit, operation: Operation) -> Iterator["Change"]:
        from donna.machine.changes import ChangeTaskState

        yield ChangeTaskState(TaskState.COMPLETED)

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> "Operation":  # type: ignore[override]
        data = section.merged_configs()

        if "title" not in data:
            data["title"] = section.title or "Untitled Finish Workflow"

        if "artifact_id" in data:
            raise NotImplementedError("artifact_id should not be set in FinishWorkflowKind.construct")

        data["artifact_id"] = str(artifact_id)

        return self.operation(**data)


finish_workflow_kind = FinishWorkflowKind(id="finish_workflow", title="Finish Workflow", operation=Operation)
