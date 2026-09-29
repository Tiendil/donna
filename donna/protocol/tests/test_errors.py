import pytest
from llm_tool_cli.core.errors import EnvironmentError
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.logic_cells import EnvironmentErrorCell

from donna.domain.artifact_ids import ArtifactId
from donna.machine.errors import ArtifactPrimarySectionMissing
from donna.protocol.errors import EnvironmentErrorNode, environment_error_node


class TestEnvironmentErrorNode:
    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_status__uses_shared_projection_for_artifact_errors(self, protocol: Protocol) -> None:
        error = ArtifactPrimarySectionMissing(artifact_id=ArtifactId("@/workflow.donna.md"))

        cell = EnvironmentErrorNode(error).status().render(protocol)[0]

        assert cell.kind == "error"
        assert cell.meta == {
            "type": "error",
            "code": error.code,
            "artifact_id": "@/workflow.donna.md",
            "section_id": None,
        }
        assert cell.content is not None
        assert cell.content.startswith(error.format_message())
        assert "Way to fix:" in cell.content

    def test_status__retains_typed_error(self) -> None:
        error = EnvironmentError(code="sample", message="First line.\nSecond line.")

        cell = EnvironmentErrorNode(error).status()

        assert isinstance(cell, EnvironmentErrorCell)
        assert cell.error == error

    def test_journal_message__renders_single_line_message(self) -> None:
        error = EnvironmentError(code="sample", message="First line.\nSecond line.")

        assert EnvironmentErrorNode(error).journal_message() == "First line. Second line."


class TestEnvironmentErrorNodeShortcut:
    def test_returns_environment_error_node(self) -> None:
        error = EnvironmentError(code="sample", message="Problem")

        node = environment_error_node(error)

        assert isinstance(node, EnvironmentErrorNode)
        assert node.status().error == error
