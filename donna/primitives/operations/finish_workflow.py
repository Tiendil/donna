import sys
from typing import TYPE_CHECKING, ClassVar, Iterator, Literal, cast

from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter
from donna.workspaces import markdown
from donna.workspaces.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class FinishWorkflowConfig(OperationConfig):
    fsm_mode: Literal[FsmMode.final] = FsmMode.final


class FinishWorkflow(MarkdownSectionMixin, OperationKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeFinishTask

        context: dict[str, object] = {
            "scheme": operation,
            "task": task,
            "work_unit": unit,
        }
        output_text = operation.description.format(**context)

        output_cell = Cell.build_markdown(
            kind="operation_output",
            content=output_text,
            operation_id=str(unit.operation_id),
        )
        formatter = get_cell_formatter()
        sys.stdout.buffer.write(formatter.format_cell(output_cell, single_mode=False) + b"\n\n")
        sys.stdout.buffer.flush()

        yield ChangeFinishTask(task_id=task.id)

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
