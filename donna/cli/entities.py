from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.paths import UntrustedPath
from llm_tool_cli.protocol import Protocol

GLOBAL_OPTIONS_CONTEXT_KEY = "donna_global_options"


class GlobalOptions(BaseEntity):
    protocol: Protocol
    config_path: UntrustedPath | None = None
