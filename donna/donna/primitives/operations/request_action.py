import re
from typing import TYPE_CHECKING, ClassVar, Iterator, cast

import pydantic

from donna.domain.ids import ArtifactSectionId, FullArtifactId
from donna.machine.action_requests import ActionRequest
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.operations import FsmMode, OperationConfig, OperationKind, OperationMeta
from donna.world import markdown
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


def extract_transitions(text: str) -> set[ArtifactSectionId]:
    """Extracts all transitions from the text of action request.

    Transition is specified as render of `goto` directive in the format:
    ```
    $$donna goto <full_artifact_local_id> donna$$
    ```
    """
    pattern = r"\$\$donna\s+goto\s+([a-zA-Z0-9_\-./:]+)\s+donna\$\$"
    matches = re.findall(pattern, text)

    transitions: set[ArtifactSectionId] = set()

    for match in matches:
        transitions.add(ArtifactSectionId.parse(match))

    return transitions


class RequestActionConfig(OperationConfig):
    @pydantic.field_validator("fsm_mode", mode="after")
    @classmethod
    def validate_fsm_mode(cls, v: FsmMode) -> FsmMode:
        if v == FsmMode.final:
            raise ValueError("RequestAction operation cannot have 'final' fsm_mode")

        return v


class RequestAction(MarkdownSectionMixin, OperationKind):
    config_class: ClassVar[type[RequestActionConfig]] = RequestActionConfig

    def markdown_construct_meta(
        self,
        artifact_id: "FullArtifactId",
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> ArtifactSectionMeta:
        request_config = cast(RequestActionConfig, section_config)
        analysis = source.as_analysis_markdown(with_title=True)

        return OperationMeta(
            fsm_mode=request_config.fsm_mode,
            allowed_transtions=extract_transitions(analysis),
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
        assert operation.id == full_operation_id.local_id

        request = ActionRequest.build(request_text, full_operation_id)

        yield ChangeAddActionRequest(action_request=request)
