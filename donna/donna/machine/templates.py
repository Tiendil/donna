from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta


class DirectiveKind(BaseEntity):
    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("You MUST implement this method.")


class DirectiveConfig(ArtifactSectionConfig):
    analyze_id: str


class DirectiveSectionMeta(ArtifactSectionMeta):
    analyze_id: str
    attribute_value: Any | None = None

    def cells_meta(self) -> dict[str, Any]:
        meta = {"analyze_id": self.analyze_id}

        if self.attribute_value is not None:
            meta["attribute_value"] = repr(self.attribute_value)

        return meta


def load_directive_section(directive_kind_id: FullArtifactLocalId) -> "ArtifactSection":
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(directive_kind_id.full_artifact_id)
    section = artifact.get_section(directive_kind_id)

    if section is None or section.entity is None or not isinstance(section.entity, DirectiveKind):
        raise NotImplementedError(f"Directive kind '{directive_kind_id}' is not available")

    return section


def resolve_directive_kind(directive_kind_id: FullArtifactLocalId) -> DirectiveKind:
    return load_directive_section(directive_kind_id).entity  # type: ignore[return-value]
