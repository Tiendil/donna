import pytest
from llm_tool_cli.core.settings import ToolLabel, initialize
from llm_tool_cli.core.tests.fixtures import isolated_settings
from pytest_mock import MockerFixture

from donna.workspaces import config as workspace_config

__all__ = ["isolated_settings"]


@pytest.fixture(autouse=True)
def initialized_settings(isolated_settings: None) -> None:
    initialize(tool_label=ToolLabel("DONNA"))


@pytest.fixture(autouse=True)
def isolated_workspace_globals(mocker: MockerFixture) -> None:
    mocker.patch.object(workspace_config.project_dir, "_value", None)
    mocker.patch.object(workspace_config.config_path, "_value", None)
    mocker.patch.object(workspace_config.config, "_value", None)
    mocker.patch.object(workspace_config.protocol, "_value", None)
