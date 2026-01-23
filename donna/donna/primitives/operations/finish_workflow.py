from typing import TYPE_CHECKING, Iterator, Literal

from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import ArtifactSection
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

    def from_markdown_section(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, object],
    ) -> ArtifactSection:
        section_config = FinishWorkflowConfig.parse_obj(config)
        description = source.as_original_markdown(with_title=False)

        return ArtifactSection(
            id=section_config.id,
            kind=section_config.kind,
            title=source.title or "",
            description=description,
            meta=OperationMeta(fsm_mode=section_config.fsm_mode, allowed_transtions=set()),
        )
