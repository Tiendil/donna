import pathlib

import pytest
from llm_tool_cli.config import create_config
from llm_tool_cli.config import errors as config_errors
from pytest_mock import MockerFixture

from donna.domain.constants import DONNA_CONFIG_NAME
from donna.protocol.modes import Mode
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors
from donna.workspaces.config import GlobalConfig
from donna.workspaces.initialization import initialize_runtime, initialize_workspace


@pytest.fixture(autouse=True)
def isolated_workspace_globals(mocker: MockerFixture) -> None:
    mocker.patch.object(workspace_config.project_dir, "_value", None)
    mocker.patch.object(workspace_config.config_path, "_value", None)
    mocker.patch.object(workspace_config.config, "_value", None)
    mocker.patch.object(workspace_config.protocol, "_value", None)


class TestInitializeRuntime:
    def test_explicit_config_path__loads_workspace(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text(
            'version = 1\nsession_dir = ".session/custom"\nworkflow_dirs = ["workflows", "workflows"]\n',
            encoding="utf-8",
        )

        workspace = initialize_runtime(config_path=config_path)
        assert workspace.root == tmp_path
        assert workspace.config_path == config_path
        assert workspace.config.session_dir == pathlib.Path(".session/custom")
        assert workspace.config.workflow_dirs == [pathlib.Path("workflows")]

    def test_relative_config_path__resolves_from_current_directory(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = tmp_path / "custom.toml"
        config_path.write_text("version = 1", encoding="utf-8")
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        workspace = initialize_runtime(config_path=pathlib.Path("custom.toml"))

        assert workspace.config_path == config_path
        assert workspace.root == tmp_path

    def test_explicit_symlink__uses_target_directory(self, tmp_path: pathlib.Path) -> None:
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        target = target_dir / "custom.toml"
        target.write_text("version = 1", encoding="utf-8")
        link = tmp_path / DONNA_CONFIG_NAME
        link.symlink_to(target)

        workspace = initialize_runtime(config_path=link)

        assert workspace.config_path == target
        assert workspace.root == target_dir

    def test_discovered_symlink__keeps_discovery_directory(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        target = target_dir / "custom.toml"
        target.write_text("version = 1", encoding="utf-8")
        link = tmp_path / DONNA_CONFIG_NAME
        link.symlink_to(target)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        workspace = initialize_runtime()

        assert workspace.config_path == link
        assert workspace.root == tmp_path

    def test_toml_1_1__loads_multiline_inline_table(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text(
            'version = 1\ndefaults = {\n    primary_section_id = "workflow",\n}\n',
            encoding="utf-8",
        )

        result = initialize_runtime(config_path=config_path)

        assert result.config.defaults.primary_section_id == "workflow"

    def test_discovery__uses_nearest_project_config(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        (tmp_path / DONNA_CONFIG_NAME).write_text("version = 1", encoding="utf-8")
        project_dir = tmp_path / "project"
        nested_dir = project_dir / "nested"
        nested_dir.mkdir(parents=True)
        config_path = project_dir / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")
        mocker.patch("pathlib.Path.cwd", return_value=nested_dir)

        result = initialize_runtime()

        assert result.root == project_dir
        assert result.config_path == config_path

    def test_discovery__raises_shared_missing_config_error(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        mocker.patch("llm_tool_cli.config.files.find_config", return_value=None)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        with pytest.raises(config_errors.NotFound) as raised:
            initialize_runtime()

        assert raised.value.code == "config_not_found"
        assert raised.value.path == tmp_path
        assert DONNA_CONFIG_NAME in raised.value.reason

    def test_missing_explicit_config__raises_shared_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        with pytest.raises(config_errors.Unreadable) as raised:
            initialize_runtime(config_path=config_path)

        assert raised.value.path == config_path
        assert isinstance(raised.value.__cause__, FileNotFoundError)

    def test_invalid_toml__raises_shared_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = ", encoding="utf-8")

        with pytest.raises(config_errors.InvalidToml) as raised:
            initialize_runtime(config_path=config_path)

        assert raised.value.code == "config_invalid_toml"
        assert raised.value.path == config_path
        assert raised.value.reason

    @pytest.mark.parametrize(
        ("config_text", "field"),
        [
            ("version = 2", "version"),
            ('session_dir = "../outside"', "session_dir"),
            ('workflow_dirs = ["/absolute"]', "workflow_dirs"),
            ("[journal]\ncmd = []", "journal.cmd"),
        ],
    )
    def test_invalid_config_schema__raises_shared_error(
        self, tmp_path: pathlib.Path, config_text: str, field: str
    ) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text(config_text, encoding="utf-8")

        with pytest.raises(config_errors.ValidationFailed) as raised:
            initialize_runtime(config_path=config_path)

        assert raised.value.code == "config_validation_failed"
        assert raised.value.path == config_path
        assert field in raised.value.reason

    def test_unknown_config_fields__raise_shared_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("[defaults]\nunknown = true\n", encoding="utf-8")

        with pytest.raises(config_errors.ValidationFailed) as raised:
            initialize_runtime(config_path=config_path)

        assert "defaults.unknown" in raised.value.reason

    def test_reports_discovery_failure(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        failure = config_errors.DiscoveryFailed(tmp_path, "permission denied")
        mocker.patch(
            "llm_tool_cli.config.files.find_config",
            side_effect=failure,
        )

        with pytest.raises(config_errors.DiscoveryFailed) as raised:
            initialize_runtime()

        assert raised.value == failure

    def test_invalid_utf8__raises_shared_error(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_bytes(b"\xff")

        with pytest.raises(config_errors.InvalidEncoding) as raised:
            initialize_runtime(config_path=config_path)

        assert raised.value.path == config_path
        assert isinstance(raised.value.__cause__, UnicodeDecodeError)

    def test_unreadable_config__propagates_shared_error(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")
        failure = config_errors.Unreadable(config_path, "permission denied")
        mocker.patch(
            "donna.workspaces.initialization.load_config",
            side_effect=failure,
        )

        with pytest.raises(config_errors.Unreadable) as raised:
            initialize_runtime(config_path=config_path)

        assert raised.value == failure

    def test_path_resolution_failure__propagates_shared_error(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        failure = config_errors.PathResolutionFailed(config_path, "symlink loop")
        mocker.patch(
            "llm_tool_cli.config.files.resolve_config_path",
            side_effect=failure,
        )

        with pytest.raises(config_errors.PathResolutionFailed) as raised:
            initialize_runtime(config_path=config_path)

        assert raised.value == failure

    def test_loads_workspace_installs_protocol_and_workspace(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        protocol = GlobalConfig[Mode]()
        mocker.patch.object(workspace_config, "protocol", protocol)
        install_workspace = mocker.patch("donna.workspaces.config.install_workspace")
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")

        workspace = initialize_runtime(config_path=config_path, protocol=Mode.llm)
        assert protocol.get() == Mode.llm
        install_workspace.assert_called_once_with(workspace)

    def test_loads_workspace_without_protocol_override(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        protocol = GlobalConfig[Mode]()
        mocker.patch.object(workspace_config, "protocol", protocol)
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")

        initialize_runtime(config_path=config_path)

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
        config_path = tmp_path / "missing" / DONNA_CONFIG_NAME
        with pytest.raises(config_errors.Unwritable) as raised:
            initialize_workspace(config_path)

        assert raised.value.path == config_path
        assert not config_path.parent.exists()

    def test_rejects_existing_config(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        config_path.write_text("version = 1", encoding="utf-8")

        with pytest.raises(config_errors.AlreadyExists) as raised:
            initialize_workspace(config_path)

        assert raised.value.path == config_path
        assert config_path.read_text(encoding="utf-8") == "version = 1"

    def test_concurrent_creation__preserves_existing_config(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME

        def create_concurrently(path: pathlib.Path, text: str) -> None:
            path.write_text("version = 1", encoding="utf-8")
            create_config(path, text)

        mocker.patch("donna.workspaces.initialization.create_config", side_effect=create_concurrently)

        with pytest.raises(config_errors.AlreadyExists) as raised:
            initialize_workspace(config_path)

        assert raised.value.path == config_path
        assert config_path.read_text(encoding="utf-8") == "version = 1"

    def test_write_failure__propagates_shared_error(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        failure = config_errors.Unwritable(config_path, "read-only filesystem")
        mocker.patch(
            "donna.workspaces.initialization.create_config",
            side_effect=failure,
        )

        with pytest.raises(config_errors.Unwritable) as raised:
            initialize_workspace(config_path)

        assert raised.value == failure

    def test_path_resolution_failure__propagates_shared_error(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        failure = config_errors.PathResolutionFailed(config_path, "symlink loop")
        mocker.patch("donna.workspaces.initialization.resolve_config_path", side_effect=failure)

        with pytest.raises(config_errors.PathResolutionFailed) as raised:
            initialize_workspace(config_path)

        assert raised.value == failure


class TestConfigCreateFailed:

    @pytest.mark.parametrize(
        "failure",
        [OSError("missing template"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte")],
    )
    def test_template_read_failure__returns_create_error(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, failure: OSError | UnicodeDecodeError
    ) -> None:
        config_path = tmp_path / DONNA_CONFIG_NAME
        mocker.patch("donna.workspaces.initialization.importlib.resources.files", side_effect=failure)

        result = initialize_workspace(config_path)

        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.ConfigCreateFailed)
        assert error.config_path == config_path
        assert error.details == str(failure)
        assert not config_path.exists()
