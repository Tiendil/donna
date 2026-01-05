from donna.core.entities import BaseEntity
from donna.domain.types import OperationId, WorkflowId
from donna.machine.cells import Cell


class Workflow(BaseEntity):
    id: WorkflowId
    operation_id: OperationId
    name: str
    description: str

    def cells(self) -> list[Cell]:
        return [
            Cell.build_markdown(
                kind="workflow",
                content=self.description,
                workflow_id=self.id,
                workflow_name=self.name,
            )
        ]
