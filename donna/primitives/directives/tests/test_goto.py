from pathlib import Path
from typing import Any

from donna.domain.artifact_ids import ArtifactSectionId
from donna.primitives.directives import goto
from donna.primitives.directives.goto import GoTo, GoToInvalidArguments
from donna.primitives.tests import make
from donna.protocol.modes import Mode


class TestGoTo:
    def test_prepare_arguments__requires_one_argument(self) -> None:
        result = GoTo(analyze_id="goto")._prepare_arguments(make.template_context(artifact_id=make.ARTIFACT_ID))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, GoToInvalidArguments)
        assert error.provided_count == 0

    def test_prepare_arguments__builds_artifact_section_id_in_current_artifact(self) -> None:
        result = GoTo(analyze_id="goto")._prepare_arguments(
            make.template_context(artifact_id=make.ARTIFACT_ID), "next"
        )

        assert result.is_ok()
        assert result.unwrap() == (ArtifactSectionId("@/workflows/test.donna.md:next"),)

    def test_render_view__renders_complete_action_request_command(self, mocker: Any) -> None:
        mocker.patch.object(goto.workspace_config, "protocol", return_value=Mode.llm)
        mocker.patch.object(goto.workspace_config, "config_path", return_value=Path("/project/donna.toml"))

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
