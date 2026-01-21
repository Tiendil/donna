"""Python artifact that exposes section kind definitions."""

from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import ArtifactConfig, ArtifactConstructor
from donna.std.code.operations import (  # noqa: F401
    finish_workflow_kind,
    python_module_section_kind,
    request_action_kind,
    text_section_kind,
)

artifact = ArtifactConstructor(
    title="Operation Section Kinds",
    description="Definitions for operation-related section kinds exposed as Python module sections.",
    config=ArtifactConfig(kind=FullArtifactLocalId.parse("donna.artifacts:python")),
)

__all__ = [
    "artifact",
    "finish_workflow_kind",
    "python_module_section_kind",
    "request_action_kind",
    "text_section_kind",
]
