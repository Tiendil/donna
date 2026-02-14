from typing import TYPE_CHECKING, ClassVar, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactSectionId, FullArtifactId
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.errors import ArtifactValidationError
from donna.machine.operations import OperationConfig, OperationKind, OperationMeta
from donna.protocol.utils import instant_output
from donna.workspaces import markdown
from donna.workspaces.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class OutputMissingNextOperation(ArtifactValidationError):
    code: str = "donna.workflows.output_missing_next_operation_id"
    message: str = "Output operation `{error.section_id}` must define `next_operation_id`."
    ways_to_fix: list[str] = [
        'Add `next_operation_id = "<next_operation_id>"` to the operation config block.',
    ]


class OutputConfig(OperationConfig):
    next_operation_id: ArtifactSectionId | None = None


class OutputMeta(OperationMeta):
    next_operation_id: ArtifactSectionId | None = None


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
        if output_config.next_operation_id is not None:
            allowed_transitions.add(output_config.next_operation_id)

        return Ok(
            OutputMeta(
                fsm_mode=output_config.fsm_mode,
                allowed_transtions=allowed_transitions,
                next_operation_id=output_config.next_operation_id,
            )
        )

    @unwrap_to_error
    def execute_section(
        self, task: "Task", unit: "WorkUnit", operation: ArtifactSection
    ) -> Result[list["Change"], ErrorsList]:
        from donna.machine import journal as machine_journal
        from donna.machine.changes import ChangeAddWorkUnit

        meta = cast(OutputMeta, operation.meta)

        journal_record = machine_journal.add(
            actor_id="donna",
            message=operation.description.strip(),
            current_task_id=str(task.id),
            current_work_unit_id=str(unit.id),
            current_operation_id=str(unit.operation_id),
        ).unwrap()

        instant_output(journal_record)

        next_operation_id = meta.next_operation_id
        assert next_operation_id is not None
        full_operation_id = unit.operation_id.full_artifact_id.to_full_local(next_operation_id)

        return Ok([ChangeAddWorkUnit(task_id=task.id, operation_id=full_operation_id)])

    def validate_section(self, artifact: Artifact, section_id: ArtifactSectionId) -> Result[None, ErrorsList]:
        section = artifact.get_section(section_id).unwrap()
        meta = cast(OutputMeta, section.meta)

        if meta.next_operation_id is None:
            return Err([OutputMissingNextOperation(artifact_id=artifact.id, section_id=section_id)])

        return Ok(None)
