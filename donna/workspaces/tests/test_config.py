import pathlib

import pydantic
import pytest
from llm_tool_cli.output.journal import JournalConfig
from llm_tool_cli.paths import RelativeProjectPath

from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.python_path import PythonPath
from donna.workspaces import config as workspace_config
from donna.workspaces.config import Config, DefaultsConfig


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
        config = Config.model_validate({"workflow_dirs": ["workflows", "./workflows", ".session/donna"]})

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
        config = Config(
            workflow_dirs=[
                RelativeProjectPath(pathlib.Path("workflows")),
                RelativeProjectPath(pathlib.Path(".session/donna")),
            ]
        )

        assert config.model_dump(mode="json")["workflow_dirs"] == ["./workflows", "./.session/donna"]
