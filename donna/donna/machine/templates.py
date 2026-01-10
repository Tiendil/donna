import jinja2

from typing import TYPE_CHECKING, Iterable, Any

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId, FullArtifactLocalId, OperationId
from donna.domain.types import OperationResultId, Slug
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource


class RendererKind(BaseEntity):
    id: str
    name: str

    @jinja2.pass_context
    def __call__(self, context, **kwargs) -> Any:
        raise NotImplementedError("You MUST implement this method.")
