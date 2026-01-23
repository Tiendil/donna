from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta, resolve


class DirectiveKind(BaseEntity):
    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("You MUST implement this method.")


class DirectiveConfig(ArtifactSectionConfig):
    analyze_id: str


class DirectiveSectionMeta(ArtifactSectionMeta):
    analyze_id: str
    directive: DirectiveKind

    model_config = BaseEntity.model_config | {"arbitrary_types_allowed": True}

    def cells_meta(self) -> dict[str, Any]:
        return {"analyze_id": self.analyze_id, "directive": repr(self.directive)}


def load_directive_section(directive_kind_id: FullArtifactLocalId) -> "ArtifactSection":
    section = resolve(directive_kind_id)

    if not isinstance(section.meta, DirectiveSectionMeta):
        raise NotImplementedError(f"Directive kind '{directive_kind_id}' is not available")

    return section
