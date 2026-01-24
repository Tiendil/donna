from typing import TYPE_CHECKING, ClassVar, Iterator, Literal, cast

from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.world import markdown
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflowKind(MarkdownSectionMixin, OperationKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        yield ChangeFinishTask(task_id=task.id)

    config_class: ClassVar[type[FinishWorkflowConfig]] = FinishWorkflowConfig

    def markdown_construct_meta(
        self,
        artifact_id: "FullArtifactId",
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> ArtifactSectionMeta:
        finish_config = cast(FinishWorkflowConfig, section_config)
        return OperationMeta(fsm_mode=finish_config.fsm_mode, allowed_transtions=set())
