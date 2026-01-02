
from donna.domain.types import SpecificationId
from donna.machine.specifications import SpecificationSource, Specification, SpecificationIndexItem


class StaticSpecificationSource(SpecificationSource):
    specifications: list[Specification]

    def list_specifications(self) -> list["SpecificationIndexItem"]:
        return [spec.item for spec in self.specifications]

    def get_specification(self,
                          specification_id: SpecificationId) -> Specification | None:
        for spec in self.specifications:
            if spec.item.id == specification_id:
                return spec

        return None
