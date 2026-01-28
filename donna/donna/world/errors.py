from donna.core import errors as core_errors
from donna.domain.ids import WorldId


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.world."""


class WorldError(core_errors.EnvironmentError):
    cell_kind: str = "world_error"


class WorldNotConfigured(WorldError):
    code: str = "donna.world.world_not_configured"
    message: str = "World with id `{error.world_id}` is not configured"
    world_id: WorldId


class SourceConfigNotConfigured(WorldError):
    code: str = "donna.world.source_config_not_configured"
    message: str = "Source config `{error.kind}` is not configured"
    kind: str


class GlobalConfigAlreadySet(InternalError):
    message = "Global config value is already set"


class GlobalConfigNotSet(InternalError):
    message = "Global config value is not set"
