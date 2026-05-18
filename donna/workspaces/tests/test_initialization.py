import pathlib

from pytest_mock import MockerFixture

from donna.core.result import Ok
from donna.domain.constants import DONNA_CONFIG_NAME
from donna.protocol.modes import Mode
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors
from donna.workspaces.config import GlobalConfig
from donna.workspaces.initialization import initialize_runtime, initialize_workspace, load_workspace


class TestLoadWorkspace:
    def test_explicit_config_path__loads_workspace(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text(
            'version = 1\nsession_dir = ".session/custom"\nworkflow_dirs = ["workflows", "workflows"]\n',
            encoding="utf-8",
        )

        result = load_workspace(config_path=config_path)

        assert result.is_ok()
        workspace = result.unwrap()
        assert workspace.root == tmp_path
        assert workspace.config_path == config_path
        assert workspace.config.session_dir == pathlib.Path(".session/custom")
        assert workspace.config.workflow_dirs == [pathlib.Path("workflows")]

    def test_discovery__uses_nearest_project_config(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")
        mocker.patch("donna.workspaces.utils.discover_project_dir", return_value=Ok(tmp_path))

        result = load_workspace()

        assert result.is_ok()
        assert result.unwrap().root == tmp_path

    def test_missing_explicit_config__returns_not_found_error(self, tmp_path: pathlib.Path) -> None:
        result = load_workspace(config_path=tmp_path / DONNA_CONFIG_NAME)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.WorkspaceConfigNotFound)

    def test_invalid_toml__returns_parse_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = ", encoding="utf-8")

        result = load_workspace(config_path=config_path)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.ConfigParseFailed)

    def test_invalid_config_schema__returns_validation_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 2", encoding="utf-8")

        result = load_workspace(config_path=config_path)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.ConfigValidationFailed)

    def test_unknown_config_fields__return_validation_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("[defaults]\nunknown = true\n", encoding="utf-8")

        result = load_workspace(config_path=config_path)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.ConfigValidationFailed)


class TestInitializeRuntime:
    def test_loads_workspace_installs_protocol_and_workspace(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        protocol = GlobalConfig[Mode]()
        mocker.patch.object(workspace_config, "protocol", protocol)
        install_workspace = mocker.patch("donna.workspaces.config.install_workspace")
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")

        result = initialize_runtime(config_path=config_path, protocol=Mode.llm)

        assert result.is_ok()
        workspace = result.unwrap()
        assert protocol.get() == Mode.llm
        install_workspace.assert_called_once_with(workspace)

    def test_loads_workspace_without_protocol_override(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        protocol = GlobalConfig[Mode]()
        mocker.patch.object(workspace_config, "protocol", protocol)
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")

        result = initialize_runtime(config_path=config_path)

        assert result.is_ok()
        assert not protocol.is_set()


class TestInitializeWorkspace:
    def test_creates_starter_config_and_loads_workspace(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        install_workspace = mocker.patch("donna.workspaces.config.install_workspace")
        config_path = tmp_path / DONNA_CONFIG_NAME

        result = initialize_workspace(config_path)

        assert result.is_ok()
        assert config_path.is_file()
        config_text = config_path.read_text(encoding="utf-8")
        assert "version = 1" in config_text
        assert 'session_dir = ".session/donna"' in config_text
        assert '"./workflows"' in config_text
        assert '"./.session/donna"' in config_text
        assert "# [defaults]" in config_text
        assert "# [journal]" in config_text
        assert "# cmd = [" in config_text
        workspace = result.unwrap()
        assert workspace.root == tmp_path
        install_workspace.assert_called_once_with(workspace)

    def test_rejects_missing_config_directory(self, tmp_path: pathlib.Path) -> None:
        result = initialize_workspace(tmp_path / "missing" / DONNA_CONFIG_NAME)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.WorkspaceConfigDirNotFound)

    def test_rejects_existing_config(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")

        result = initialize_workspace(config_path)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.WorkspaceAlreadyInitialized)
