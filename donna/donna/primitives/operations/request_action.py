import re
from typing import TYPE_CHECKING, Iterator

import pydantic

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.action_requests import ActionRequest
from donna.machine.artifacts import ArtifactSection
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.world import markdown

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


def extract_transitions(text: str) -> set[FullArtifactLocalId]:
    """Extracts all transitions from the text of action request.

    Transition is specified as render of `goto` directive in the format:
    ```
    $$donna goto <full_artifact_local_id> donna$$
    ```
    """
    pattern = r"\$\$donna\s+goto\s+([a-zA-Z0-9_\-./]+)\s+donna\$\$"
    matches = re.findall(pattern, text)

    transitions: set[FullArtifactLocalId] = set()

    for match in matches:
        transitions.add(FullArtifactLocalId.parse(match))

    return transitions


class RequestActionConfig(OperationConfig):
    @pydantic.field_validator("fsm_mode", mode="after")
    @classmethod
    def validate_fsm_mode(cls, v: FsmMode) -> FsmMode:
        if v == FsmMode.final:
            raise ValueError("RequestAction operation cannot have 'final' fsm_mode")

        return v


class RequestActionKind(OperationKind):
    def from_markdown_section(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, object],
    ) -> ArtifactSection:
        section_config = RequestActionConfig.parse_obj(config)
        description = source.as_original_markdown(with_title=False)
        analysis = source.as_analysis_markdown(with_title=True)

        return ArtifactSection(
            id=section_config.id,
            kind=section_config.kind,
            title=source.title or "",
            description=description,
            meta=OperationMeta(
                fsm_mode=section_config.fsm_mode,
                allowed_transtions=extract_transitions(analysis),
            ),
        )

    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddActionRequest

        context: dict[str, object] = {
            "scheme": operation,
            "task": task,
            "work_unit": unit,
        }

        request_text = operation.description.format(**context)

        full_operation_id = unit.operation_id
        assert operation.id is not None
        assert operation.id == full_operation_id.local_id

        request = ActionRequest.build(request_text, full_operation_id)

        yield ChangeAddActionRequest(action_request=request)
