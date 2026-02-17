from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.domain.ids import WorldId
from donna.workspaces.config import config
from donna.workspaces.worlds.base import World


@unwrap_to_error
def session_world() -> Result[World, ErrorsList]:
    world = config().get_world(WorldId("session")).unwrap()

    if not world.is_initialized():
        world.initialize(reset=False)

    return Ok(world)
