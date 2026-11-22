import pathlib

import pydantic
import pytest
from llm_tool_cli.output.journal import JournalConfig

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


class TestConfig:
    def test_defaults__match_configuration_spec(self) -> None:
        config = Config()

        assert config.version == 1
        assert config.session_dir == pathlib.Path(".session/donna")
        assert config.workflow_dirs == [pathlib.Path("workflows"), pathlib.Path(".session/donna")]
        assert config.template_dirs == []
        assert config.journal == JournalConfig()

    @pytest.mark.parametrize("field", ["workflow_dirs", "template_dirs"])
    def test_validate_project_dirs__deduplicates_preserving_order(self, field: str) -> None:
        config = Config.model_validate({field: ["first", "./first", "second"]})

        assert getattr(config, field) == [pathlib.Path("first"), pathlib.Path("second")]

    @pytest.mark.parametrize("field", ["session_dir", "workflow_dirs", "template_dirs"])
    def test_validation__rejects_absolute_project_paths(self, field: str) -> None:
        value = pathlib.Path("/outside")
        data = {field: value if field == "session_dir" else [value]}

        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(data)

    @pytest.mark.parametrize("field", ["session_dir", "workflow_dirs", "template_dirs"])
    def test_validation__rejects_parent_directory_references(self, field: str) -> None:
        value = pathlib.Path("../outside")
        data = {field: value if field == "session_dir" else [value]}

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

    @pytest.mark.parametrize("field", ["workflow_dirs", "template_dirs"])
    def test_model_dump__serializes_project_dirs_as_project_relative_strings(self, field: str) -> None:
        config = Config.model_validate({field: ["first", "second"]})

        assert config.model_dump(mode="json")[field] == ["./first", "./second"]
