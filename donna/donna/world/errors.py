
import pathlib

from donna.core.errors import EnvironmentError, ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactId, FullArtifactIdPattern
from donna.machine.artifacts import Artifact
from donna.world.config import config


class WorldError(EnvironmentError):
    cell_kind: str = "world_error"
