from typing import TYPE_CHECKING, ClassVar, Iterator, Literal

from donna.machine.artifacts import ArtifactSection, ArtifactSectionMeta
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.world import markdown

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflowKind(OperationKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        yield ChangeFinishTask(task_id=task.id)

    config_class: ClassVar[type[FinishWorkflowConfig]] = FinishWorkflowConfig

    def construct_meta(
        self,
        artifact_id: "FullArtifactId",
        source: markdown.SectionSource,
        section_config: FinishWorkflowConfig,
        description: str,
        primary: bool = False,
    ) -> ArtifactSectionMeta:
        return OperationMeta(fsm_mode=section_config.fsm_mode, allowed_transtions=set())
