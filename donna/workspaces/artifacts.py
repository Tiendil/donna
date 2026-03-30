import pathlib

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces.config import config
from donna.workspaces.templates import RenderMode


class ArtifactRenderContext(BaseEntity):
    primary_mode: RenderMode
    current_task: Task | None = None
    current_work_unit: WorkUnit | None = None


RENDER_CONTEXT_VIEW = ArtifactRenderContext(primary_mode=RenderMode.view)


@unwrap_to_error
def artifact_file_extension(full_id: FullArtifactId) -> Result[str, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()
    return Ok(world.file_extension_for(full_id.artifact_id).unwrap().lstrip("."))


@unwrap_to_error
def fetch_artifact(full_id: FullArtifactId, output: pathlib.Path) -> Result[None, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()
    raw_artifact = world.fetch(full_id.artifact_id).unwrap()

    with output.open("wb") as f:
        f.write(raw_artifact.get_bytes())

    return Ok(None)
