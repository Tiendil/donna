import pytest
from llm_tool_cli.protocol import Protocol

from donna.machine.tests import make as machine_make
from donna.protocol.logic_cells.tests import make
from donna.protocol.logic_cells.tests.helpers import project


class TestArtifactSectionStatusCell:
    def test_markdown_blocks__uses_section_heading_and_description(self) -> None:
        assert make.section().markdown_blocks() == ["## Step", "Description"]

    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__preserves_section_payload_and_extension_metadata(self, protocol: Protocol) -> None:
        cell = make.section(section_primary=True, extra_meta={"custom": ["first", "second"]})

        output = project(cell, protocol)

        assert output.model_dump(exclude={"id"}) == {
            "kind": "artifact_section_status",
            "media_type": "text/markdown",
            "content": "## Step\nDescription",
            "meta": {
                "artifact_id": str(machine_make.ARTIFACT_ID),
                "section_id": str(machine_make.PRIMARY_SECTION_ID),
                "section_kind": str(machine_make.PRIMITIVE_PATH),
                "section_primary": True,
                "custom": ["first", "second"],
            },
        }

    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__preserves_extension_override_precedence(self, protocol: Protocol) -> None:
        cell = make.section(section_primary=True, extra_meta={"section_primary": False, "content": "extra"})

        output = project(cell, protocol)

        assert not output.meta["section_primary"]
        assert output.meta["content"] == "extra"
        assert output.content == "## Step\nDescription"
        assert cell.section_primary
