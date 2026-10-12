from pathlib import Path

import pytest
from llm_tool_cli.config.project import ProjectConfig, project_config
from llm_tool_cli.config.runtime import RuntimeConfig, runtime_config
from llm_tool_cli.config.tests.fixtures import runtime_settings
from llm_tool_cli.core.errors import ContextValueNotSet
from llm_tool_cli.paths import ProjectConfigPath
from llm_tool_cli.protocol import Protocol
from pytest_mock import MockerFixture

from donna.domain.artifact_ids import ArtifactSectionId
from donna.machine.tests import make as machine_make
from donna.primitives.directives.goto import GoTo, GoToInvalidArguments
from donna.primitives.tests import make


class TestGoTo:
    def test_render_view__requires_an_active_workspace(self) -> None:
        with pytest.raises(ContextValueNotSet) as caught:
            GoTo(analyze_id="goto").render_view(
                make.template_context(),
                ArtifactSectionId("@/workflows/test.donna.md:next"),
            )
        assert caught.value.details == {"name": "project_config"}

    def test_prepare_arguments__requires_one_argument(self) -> None:
        result = GoTo(analyze_id="goto")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID)
        )

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, GoToInvalidArguments)
        assert error.provided_count == 0

    def test_prepare_arguments__builds_artifact_section_id_in_current_artifact(self) -> None:
        result = GoTo(analyze_id="goto")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID), "next"
        )

        assert result.is_ok()
        assert result.unwrap() == (ArtifactSectionId("@/workflows/test.donna.md:next"),)

    def test_render_view__renders_complete_action_request_command(self, mocker: MockerFixture) -> None:
        with (
            runtime_config.scope(RuntimeConfig(protocol=Protocol.llm)),
            project_config.scope(ProjectConfig(config_path=ProjectConfigPath(Path("/project/donna.toml")))),
        ):
            result = GoTo(analyze_id="goto").render_view(
                make.template_context(),
                ArtifactSectionId("@/workflows/test.donna.md:next"),
            )

        assert result.is_ok()
        assert (
            result.unwrap() == "donna -p llm --config '/project/donna.toml' "
            "complete-action-request <action-request-id> '@/workflows/test.donna.md:next'"
        )

    def test_render_analyze__renders_section_local_marker(self) -> None:
        result = GoTo(analyze_id="goto").render_analyze(
            make.template_context(),
            ArtifactSectionId("@/workflows/test.donna.md:next"),
        )

        assert result.is_ok()
        assert result.unwrap() == "$$donna goto next donna$$"


__all__ = ["runtime_settings"]

pytestmark = pytest.mark.usefixtures("runtime_settings")
