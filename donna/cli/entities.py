import pathlib

from donna.core.entities import BaseEntity
from donna.protocol.modes import Mode

GLOBAL_OPTIONS_CONTEXT_KEY = "donna_global_options"


class GlobalOptions(BaseEntity):
    protocol: Mode
    root_dir: pathlib.Path | None = None
