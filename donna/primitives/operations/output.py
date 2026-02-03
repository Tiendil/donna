import sys
from typing import TYPE_CHECKING, ClassVar, Iterator, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import ArtifactSectionId, FullArtifactId
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.errors import ArtifactValidationError
from donna.machine.operations import OperationConfig, OperationKind, OperationMeta
from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter
from donna.workspaces import markdown
from donna.workspaces.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class OutputMissingNextOperation(ArtifactValidationError):
    code: str = "donna.workflows.output_missing_next_operation"
    message: str = "Output operation `{error.section_id}` must define `next_operation`."
    ways_to_fix: list[str] = [
        'Add `next_operation = "<next_operation>"` to the operation config block.',
    ]


class OutputConfig(OperationConfig):
    next_operation: ArtifactSectionId | None = None


class OutputMeta(OperationMeta):
    next_operation: ArtifactSectionId | None = None


class Output(MarkdownSectionMixin, OperationKind):
    config_class: ClassVar[type[OutputConfig]] = OutputConfig

    def markdown_construct_meta(
        self,
        artifact_id: "FullArtifactId",
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> Result[ArtifactSectionMeta, ErrorsList]:
        output_config = cast(OutputConfig, section_config)

        allowed_transitions: set[ArtifactSectionId] = set()
        if output_config.next_operation is not None:
            allowed_transitions.add(output_config.next_operation)

        return Ok(
            OutputMeta(
                fsm_mode=output_config.fsm_mode,
                allowed_transtions=allowed_transitions,
                next_operation=output_config.next_operation,
            )
        )

    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddWorkUnit

        meta = cast(OutputMeta, operation.meta)

        output_text = operation.description

        output_cell = Cell.build_markdown(
            kind="operation_output",
            content=output_text,
            operation_id=str(unit.operation_id),
        )
        formatter = get_cell_formatter()
        sys.stdout.buffer.write(formatter.format_cell(output_cell, single_mode=False) + b"\n\n")
        sys.stdout.buffer.flush()

        next_operation = meta.next_operation
        assert next_operation is not None
        full_operation_id = unit.operation_id.full_artifact_id.to_full_local(next_operation)

        yield ChangeAddWorkUnit(task_id=task.id, operation_id=full_operation_id)

    def validate_section(self, artifact: Artifact, section_id: ArtifactSectionId) -> Result[None, ErrorsList]:
        section = artifact.get_section(section_id).unwrap()
        meta = cast(OutputMeta, section.meta)

        if meta.next_operation is None:
            return Err([OutputMissingNextOperation(artifact_id=artifact.id, section_id=section_id)])

        return Ok(None)
