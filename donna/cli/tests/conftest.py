import pytest
from pytest_mock import MockerFixture

from donna.workspaces import config as workspace_config


@pytest.fixture(autouse=True)
def isolated_workspace_globals(mocker: MockerFixture) -> None:
    mocker.patch.object(workspace_config.project_dir, "_value", None)
    mocker.patch.object(workspace_config.config_path, "_value", None)
    mocker.patch.object(workspace_config.config, "_value", None)
    mocker.patch.object(workspace_config.protocol, "_value", None)
