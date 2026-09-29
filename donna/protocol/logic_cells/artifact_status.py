from llm_tool_cli.protocol.output_cells.base import OutputCell

from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath
from donna.protocol.logic_cells.base import DonnaCell


class ArtifactStatusCell(DonnaCell):
    artifact_id: ArtifactId
    artifact_kind: PythonPath
    artifact_title: str
    description: str

    def _render(self, cell_type: type[OutputCell]) -> OutputCell:
        return cell_type.build_markdown(
            kind="artifact_status",
            content=self.description,
            artifact_id=str(self.artifact_id),
            artifact_kind=str(self.artifact_kind),
            artifact_title=self.artifact_title,
        )
