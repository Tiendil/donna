import pytest
from llm_tool_cli.protocol import Protocol

from donna.machine.tests import make
from donna.protocol import ArtifactStatusCell
from donna.protocol.logic_cells.tests.helpers import project


class TestArtifactStatusCell:
    @pytest.mark.parametrize("protocol", list(Protocol))
    @pytest.mark.parametrize("description", ["Workflow description", ""])
    def test_render__preserves_summary_payload(self, protocol: Protocol, description: str) -> None:
        cell = ArtifactStatusCell(
            artifact_id=make.ARTIFACT_ID,
            artifact_kind=make.PRIMITIVE_PATH,
            artifact_title="Workflow",
            description=description,
        )

        output = project(cell, protocol)

        assert output.model_dump(exclude={"id"}) == {
            "kind": "artifact_status",
            "media_type": "text/markdown",
            "content": description,
            "meta": {
                "artifact_id": str(make.ARTIFACT_ID),
                "artifact_kind": str(make.PRIMITIVE_PATH),
                "artifact_title": "Workflow",
            },
        }
        assert project(cell, protocol).id != output.id
