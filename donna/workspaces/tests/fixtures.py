from collections.abc import Iterator

import pytest

from donna.workspaces import config as workspace_config


@pytest.fixture
def default_workspace_config() -> Iterator[None]:
    with workspace_config.config.scope(workspace_config.Config()):
        yield
