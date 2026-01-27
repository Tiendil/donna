from donna.core.errors import EnvironmentError


class WorldError(EnvironmentError):
    cell_kind: str = "world_error"
