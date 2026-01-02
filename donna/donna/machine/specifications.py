from __future__ import annotations

from donna.core.entities import BaseEntity
from donna.domain.types import SpecificationId, SpecificationSourceId
from donna.machine.cells import Cell


class SpecificationSource(BaseEntity):
    id: SpecificationSourceId

    def list_specifications(self) -> list["SpecificationIndexItem"]:
        raise NotImplementedError("You MUST implement this method.")

    def get_specification(self, specification_id: SpecificationId) -> Specification | None:
        raise NotImplementedError("You MUST implement this method.")


class SpecificationIndexItem(BaseEntity):
    id: SpecificationId
    name: str
    description: str

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="specification_index_item",
                specification_id=self.id,
                specification_name=self.name,
                specification_description=self.description,
            )
        ]


class Specification(BaseEntity):
    item: SpecificationIndexItem
    content: str

    def cells(self) -> list[Cell]:
        return [
            Cell.build_markdown(
                kind="specification",
                content=self.content,
                specification_id=self.item.id,
                specification_name=self.item.name,
                specification_description=self.item.description,
            )
        ]
