from donna.core.entities import BaseEntity
from donna.domain.paths import UntrustedPath
from donna.protocol.modes import Mode

GLOBAL_OPTIONS_CONTEXT_KEY = "donna_global_options"


class GlobalOptions(BaseEntity):
    protocol: Mode
    config_path: UntrustedPath | None = None
