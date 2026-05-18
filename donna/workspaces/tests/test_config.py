import pathlib

import pydantic
import pytest

from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.paths import ProjectConfigPath, ProjectRootPath, RelativeProjectPath
from donna.domain.python_path import PythonPath
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors
from donna.workspaces.config import Config, DefaultsConfig, GlobalConfig, JournalConfig, JournalRecordAttribute
from donna.workspaces.tests import make


class TestJournalRecordAttribute:
    def test_has_attribute__accepts_supported_attribute_names(self) -> None:
        assert JournalRecordAttribute.has_attribute("message")
        assert not JournalRecordAttribute.has_attribute("missing")


class TestIsJournalVariableArgument:
    def test_detects_whole_argument_placeholders(self) -> None:
        assert workspace_config._is_journal_variable_argument("{message}")
        assert not workspace_config._is_journal_variable_argument("literal:{message}")
        assert not workspace_config._is_journal_variable_argument("{message")


class TestJournalConfig:
    def test_validate_cmd__accepts_none_and_supported_placeholders(self) -> None:
        assert JournalConfig(cmd=None).cmd is None
        assert JournalConfig(cmd=["tool", "{message}", "literal:{message}"]).cmd == [
            "tool",
            "{message}",
            "literal:{message}",
        ]

    @pytest.mark.parametrize("cmd", [[], ["tool", "{missing}"], ["tool", 1]])
    def test_validate_cmd__rejects_invalid_command(self, cmd: list[object]) -> None:
        with pytest.raises(pydantic.ValidationError):
            JournalConfig(cmd=cmd)


class TestDefaultsConfig:
    def test_defaults__match_configuration_spec(self) -> None:
        defaults = DefaultsConfig()

        assert defaults.tail_section_kind == PythonPath(NormalizedRawIdPath("donna.lib.text"))
        assert defaults.primary_section_kind == PythonPath(NormalizedRawIdPath("donna.lib.workflow"))
        assert defaults.primary_section_id == "primary"

    @pytest.mark.parametrize(
        "data",
        [
            {"tail_section_kind": "not a python path"},
            {"primary_section_kind": "not a python path"},
            {"primary_section_id": "---"},
        ],
    )
    def test_validation__rejects_invalid_defaults(self, data: dict[str, str]) -> None:
        with pytest.raises(pydantic.ValidationError):
            DefaultsConfig.model_validate(data)


class TestDefaultWorkflowDirs:
    def test_returns_spec_defaults(self) -> None:
        assert workspace_config._default_workflow_dirs() == [
            pathlib.Path("workflows"),
            pathlib.Path(".session/donna"),
        ]


class TestSerializeWorkflowDir:
    def test_serializes_as_project_relative_string(self) -> None:
        assert (
            workspace_config._serialize_workflow_dir(RelativeProjectPath(pathlib.Path("workflows"))) == "./workflows"
        )


class TestValidateRelativeProjectPath:
    def test_returns_relative_project_path(self) -> None:
        path = RelativeProjectPath(pathlib.Path("workflows"))

        assert workspace_config._validate_relative_project_path(path) == path

    @pytest.mark.parametrize("path", [pathlib.Path("/outside"), pathlib.Path("../outside")])
    def test_rejects_invalid_project_paths(self, path: pathlib.Path) -> None:
        with pytest.raises(ValueError):
            workspace_config._validate_relative_project_path(RelativeProjectPath(path))


class TestConfig:
    def test_defaults__match_configuration_spec(self) -> None:
        config = Config()

        assert config.version == 1
        assert config.session_dir == pathlib.Path(".session/donna")
        assert config.workflow_dirs == [pathlib.Path("workflows"), pathlib.Path(".session/donna")]
        assert config.journal == JournalConfig()

    def test_validate_workflow_dirs__deduplicates_preserving_order(self) -> None:
        config = Config(workflow_dirs=["workflows", "./workflows", ".session/donna"])

        assert config.workflow_dirs == [pathlib.Path("workflows"), pathlib.Path(".session/donna")]

    @pytest.mark.parametrize("field", ["session_dir", "workflow_dirs"])
    def test_validation__rejects_absolute_project_paths(self, field: str) -> None:
        value = pathlib.Path("/outside")
        data = {field: [value] if field == "workflow_dirs" else value}

        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(data)

    @pytest.mark.parametrize("field", ["session_dir", "workflow_dirs"])
    def test_validation__rejects_parent_directory_references(self, field: str) -> None:
        value = pathlib.Path("../outside")
        data = {field: [value] if field == "workflow_dirs" else value}

        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(data)

    @pytest.mark.parametrize(
        "data",
        [
            {"unknown": True},
            {"defaults": {"unknown": True}},
            {"journal": {"unknown": True}},
        ],
    )
    def test_validation__rejects_unknown_fields(self, data: dict[str, object]) -> None:
        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(data)

    def test_model_dump__serializes_workflow_dirs_as_project_relative_strings(self) -> None:
        config = Config(workflow_dirs=["workflows", ".session/donna"])

        assert config.model_dump(mode="json")["workflow_dirs"] == ["./workflows", "./.session/donna"]


class TestGlobalConfig:
    def test_get__raises_when_value_is_not_set(self) -> None:
        global_config = GlobalConfig[str]()

        with pytest.raises(workspace_errors.GlobalConfigNotSet):
            global_config.get()

    def test_set__stores_single_value(self) -> None:
        global_config = GlobalConfig[str]()

        global_config.set("value")

        assert global_config.get() == "value"
        assert global_config()
        assert global_config.is_set()

        with pytest.raises(workspace_errors.GlobalConfigAlreadySet):
            global_config.set("other")


class TestWorkspace:
    def test_builds_validated_workspace_entity(self, tmp_path: pathlib.Path) -> None:
        workspace = make.workspace(tmp_path)

        assert workspace.root == ProjectRootPath(tmp_path)
        assert workspace.config_path == ProjectConfigPath(tmp_path / "donna.toml")
        assert workspace.config == Config()


class TestInstallWorkspace:
    def test_install_workspace__sets_unset_globals(self, mocker: object, tmp_path: pathlib.Path) -> None:
        project_dir = GlobalConfig[ProjectRootPath]()
        config_path = GlobalConfig[ProjectConfigPath]()
        config = GlobalConfig[Config]()
        mocker.patch.object(workspace_config, "project_dir", project_dir)
        mocker.patch.object(workspace_config, "config_path", config_path)
        mocker.patch.object(workspace_config, "config", config)
        workspace = make.workspace(tmp_path)

        workspace_config.install_workspace(workspace)

        assert project_dir.get() == ProjectRootPath(tmp_path)
        assert config_path.get() == ProjectConfigPath(tmp_path / "donna.toml")
        assert config.get() == workspace.config

    def test_install_workspace__does_not_replace_existing_globals(
        self, mocker: object, tmp_path: pathlib.Path
    ) -> None:
        project_dir = GlobalConfig[ProjectRootPath]()
        config_path = GlobalConfig[ProjectConfigPath]()
        config = GlobalConfig[Config]()
        project_dir.set(ProjectRootPath(tmp_path / "existing"))
        config_path.set(ProjectConfigPath(tmp_path / "existing.toml"))
        config.set(Config(session_dir="custom"))
        mocker.patch.object(workspace_config, "project_dir", project_dir)
        mocker.patch.object(workspace_config, "config_path", config_path)
        mocker.patch.object(workspace_config, "config", config)

        workspace_config.install_workspace(make.workspace(tmp_path))

        assert project_dir.get() == ProjectRootPath(tmp_path / "existing")
        assert config_path.get() == ProjectConfigPath(tmp_path / "existing.toml")
        assert config.get().session_dir == pathlib.Path("custom")
