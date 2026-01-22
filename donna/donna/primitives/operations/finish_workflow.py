from typing import TYPE_CHECKING, Iterator, Literal

from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import ArtifactSection, SectionContent
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflowKind(OperationKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        yield ChangeFinishTask(task_id=task.id)

    def construct_section(self, artifact_id: FullArtifactId, section: SectionContent) -> ArtifactSection:
        config = FinishWorkflowConfig.parse_obj(section.config)

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=OperationMeta(fsm_mode=config.fsm_mode, allowed_transtions=set()),
        )
