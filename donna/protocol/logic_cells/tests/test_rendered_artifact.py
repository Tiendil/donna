import pydantic
import pytest
from llm_tool_cli.protocol import Protocol

from donna.machine.tests import make
from donna.protocol import RenderedArtifactCell
from donna.protocol.logic_cells.tests.helpers import project


class TestRenderedArtifactCell:
    def test_model_validate__rejects_journal_delivery(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="is_journal"):
            RenderedArtifactCell.model_validate(
                {"artifact_id": make.ARTIFACT_ID, "content": "# Workflow", "is_journal": True}
            )

    @pytest.mark.parametrize("protocol", list(Protocol))
    @pytest.mark.parametrize("content", ["", "  # café\n\nDocument content\n  "])
    def test_render__preserves_document_payload(self, protocol: Protocol, content: str) -> None:
        cell = RenderedArtifactCell(artifact_id=make.ARTIFACT_ID, content=content)

        rendered = project(cell, protocol)

        assert rendered.model_dump(exclude={"id"}) == {
            "kind": "rendered_artifact",
            "media_type": "text/markdown",
            "content": content.strip(),
            "meta": {"type": "rendered_artifact"},
        }
        assert project(cell, protocol).id != rendered.id
