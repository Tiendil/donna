import shutil
from donna.core.entities import BaseEntity
from donna.domain import types
from donna.domain.types import ActionRequestId, Slug, WorkflowId
from donna.machine.cells import Cell
from donna.machine.counters import Counters
from donna.machine.plans import Plan
from donna.machine.records import RecordsIndex
from donna.machine.tasks import Task, WorkUnit
from donna.world.layout import layout
from donna.world.primitives_register import register


def start() -> None:

    plan = Plan.build()

    counters = Counters.build()

    records_index = RecordsIndex(records=[])

    shutil.rmtree(layout().session)

    layout().session.mkdir(parents=True, exist_ok=True)
    layout().session_records_dir().mkdir(parents=True, exist_ok=True)

    plan.save()

    counters.save()

    records_index.save()


def exists() -> bool:
    return layout().session_plan().exists()


def start_workflow(workflow_id: WorkflowId) -> None:
    workflow = register().workflows.get(workflow_id)
    assert workflow is not None
    operation_id = workflow.operation_id

    plan = Plan.load()

    task = Task.build()
    start = WorkUnit.build(task.id, operation_id)

    plan.add_task(task, start)

    plan.save()
