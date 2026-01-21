from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import ArtifactSectionMeta


class DirectiveKind(BaseEntity):
    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("You MUST implement this method.")


class DirectiveSectionMeta(ArtifactSectionMeta):
    name: str
    example: str

    def cells_meta(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "example": self.example,
        }


def resolve_directive_kind(directive_kind_id: FullArtifactLocalId) -> DirectiveKind:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(directive_kind_id.full_artifact_id)
    section = artifact.get_section(directive_kind_id)

    if section is None or section.entity is None or not isinstance(section.entity, DirectiveKind):
        raise NotImplementedError(f"Directive kind '{directive_kind_id}' is not available")

    return section.entity
