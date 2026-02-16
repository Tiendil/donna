from typing import TYPE_CHECKING, ClassVar, Literal, cast

from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.protocol import cell_shortcuts
from donna.protocol.utils import instant_output_cell
from donna.workspaces import markdown
from donna.workspaces.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflow(MarkdownSectionMixin, OperationKind):
    @unwrap_to_error
    def execute_section(
        self, task: "Task", unit: "WorkUnit", operation: ArtifactSection
    ) -> Result[list["Change"], ErrorsList]:
        from donna.machine.changes import ChangeFinishTask

        info = cell_shortcuts.info(operation.description)
        instant_output_cell(info)

        return Ok([ChangeFinishTask(task_id=task.id)])

    config_class: ClassVar[type[FinishWorkflowConfig]] = FinishWorkflowConfig

    def markdown_construct_meta(
        self,
        artifact_id: "FullArtifactId",
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> Result[ArtifactSectionMeta, ErrorsList]:
        finish_config = cast(FinishWorkflowConfig, section_config)
        return Ok(OperationMeta(fsm_mode=finish_config.fsm_mode, allowed_transtions=set()))
