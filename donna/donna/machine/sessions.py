import shutil
from typing import cast

from donna.domain.ids import FullArtifactId
from donna.machine.counters import Counters
from donna.machine.plans import Plan
from donna.machine.records import RecordsIndex
from donna.machine.tasks import Task, WorkUnit
from donna.std.code.workflows import Workflow
from donna.world import navigator
from donna.world.layout import layout


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


def start_workflow(artifact_id: FullArtifactId) -> None:
    workflow = cast(Workflow, navigator.get_artifact(artifact_id))

    plan = Plan.load()

    task = Task.build()
    start = WorkUnit.build(task.id, workflow.full_start_operation_id)

    plan.add_task(task, start)

    plan.save()
