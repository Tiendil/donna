import pydantic
from llm_tool_cli.protocol.output_cells.base import MetaValue, OutputCell

from donna.domain.artifact_ids import ArtifactId
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.protocol.logic_cells.base import DonnaCell


class ArtifactSectionStatusCell(DonnaCell):
    artifact_id: ArtifactId
    section_id: SectionId
    section_kind: PythonPath
    section_primary: bool
    title: str
    description: str
    extra_meta: dict[str, MetaValue] = pydantic.Field(default_factory=dict)

    def markdown_blocks(self) -> list[str]:
        return [f"## {self.title}", self.description]

    def _render(self, cell_type: type[OutputCell]) -> OutputCell:
        return cell_type(
            kind="artifact_section_status",
            media_type="text/markdown",
            content="\n".join(self.markdown_blocks()),
            meta={
                "artifact_id": str(self.artifact_id),
                "section_id": str(self.section_id),
                "section_kind": str(self.section_kind),
                "section_primary": self.section_primary,
                **self.extra_meta,
            },
        )
