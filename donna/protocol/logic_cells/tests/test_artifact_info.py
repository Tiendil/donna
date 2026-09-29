import pytest
from llm_tool_cli.protocol import Protocol

from donna.machine.tests import make as machine_make
from donna.protocol import ArtifactInfoCell
from donna.protocol.logic_cells.tests import make
from donna.protocol.logic_cells.tests.helpers import project


class TestArtifactInfoCell:
    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__preserves_headings_section_order_and_metadata(self, protocol: Protocol) -> None:
        cell = ArtifactInfoCell(
            artifact_id=machine_make.ARTIFACT_ID,
            artifact_kind=machine_make.PRIMITIVE_PATH,
            title="Workflow",
            description="Intro",
            sections=(
                make.section(title="First", description="One"),
                make.section(title="Primary", description="Already included", section_primary=True),
                make.section(title="Last", description="Two"),
            ),
        )

        output = project(cell, protocol)

        assert output.model_dump(exclude={"id"}) == {
            "kind": "artifact_info",
            "media_type": "text/markdown",
            "content": "# Workflow\nIntro\n## First\nOne\n## Last\nTwo",
            "meta": {"artifact_id": str(machine_make.ARTIFACT_ID), "artifact_kind": str(machine_make.PRIMITIVE_PATH)},
        }

    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__supports_artifact_without_other_sections(self, protocol: Protocol) -> None:
        cell = ArtifactInfoCell(
            artifact_id=machine_make.ARTIFACT_ID,
            artifact_kind=machine_make.PRIMITIVE_PATH,
            title="Workflow",
            description="",
            sections=(),
        )

        assert project(cell, protocol).content == "# Workflow"
