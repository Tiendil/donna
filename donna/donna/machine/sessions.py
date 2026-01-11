import shutil
from typing import cast

from donna.domain.ids import FullArtifactId
from donna.machine.plans import Plan
from donna.machine.tasks import Task, WorkUnit
from donna.std.code.workflows import Workflow
from donna.world import artifacts
from donna.world.layout import layout


def start() -> None:

    plan = Plan.build()

    shutil.rmtree(layout().session)

    layout().session.mkdir(parents=True, exist_ok=True)

    plan.save()


def exists() -> bool:
    return layout().session_plan().exists()


def start_workflow(artifact_id: FullArtifactId) -> None:
    workflow = cast(Workflow, artifacts.load_artifact(artifact_id))

    plan = Plan.load()

    plan.start_workflow(workflow.full_start_operation_id)

    plan.save()
