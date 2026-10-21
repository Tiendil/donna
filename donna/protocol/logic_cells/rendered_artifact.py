from typing import Literal

import pydantic
from llm_tool_cli.protocol.logic_cells.uniform import UniformCell
from llm_tool_cli.protocol.output_cells.base import OutputCell

from donna.domain.artifact_ids import ArtifactId


class RenderedArtifactCell(UniformCell):
    is_journal: Literal[False] = pydantic.Field(default=False, exclude=True)
    artifact_id: ArtifactId
    content: str

    def _render(self, cell_type: type[OutputCell]) -> OutputCell:
        return cell_type.build_markdown(kind="rendered_artifact", content=self.content, type="rendered_artifact")
