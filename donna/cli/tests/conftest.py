import pytest
from llm_tool_cli.core.settings import ConfigFilename, ToolLabel, initialize
from llm_tool_cli.core.tests.fixtures import isolated_settings

__all__ = ["isolated_settings"]


@pytest.fixture(autouse=True)
def initialized_settings(isolated_settings: None) -> None:
    initialize(label=ToolLabel("DONNA"), config_filename=ConfigFilename("donna.toml"))
