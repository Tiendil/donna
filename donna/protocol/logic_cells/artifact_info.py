from llm_tool_cli.protocol.logic_cells.uniform import UniformCell
from llm_tool_cli.protocol.output_cells.base import OutputCell

from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath
from donna.protocol.logic_cells.artifact_section_status import ArtifactSectionStatusCell


class ArtifactInfoCell(UniformCell):
    artifact_id: ArtifactId
    artifact_kind: PythonPath
    title: str
    description: str
    sections: tuple[ArtifactSectionStatusCell, ...]

    def _render(self, cell_type: type[OutputCell]) -> OutputCell:
        blocks = [f"# {self.title}", self.description]
        for section in self.sections:
            if not section.section_primary:
                blocks.extend(section.markdown_blocks())
        return cell_type.build_markdown(
            kind="artifact_info",
            content="\n".join(blocks),
            artifact_id=str(self.artifact_id),
            artifact_kind=str(self.artifact_kind),
        )
