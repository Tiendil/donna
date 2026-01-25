from __future__ import annotations

from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.world.config import SourceConfig as SourceConfigModel


class SourceConfig(BaseEntity):
    kind: str


class SourceConstructor(Primitive):
    def construct_source(self, config: SourceConfigModel) -> SourceConfig:
        raise NotImplementedError("You must implement this method in subclasses")
