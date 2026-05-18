import pathlib

from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.machine.artifacts import Artifact
from donna.machine.templates import RenderMode
from donna.protocol.journal import JournalRecord
from donna.workspaces.artifacts import ArtifactRenderContext


class FakeRawArtifact:
    def __init__(self, path: pathlib.Path, artifact: Artifact) -> None:
        self.path = path
        self.artifact = artifact
        self.render_modes: list[RenderMode] = []

    def render(self, artifact_id: object, render_context: ArtifactRenderContext) -> Result[Artifact, ErrorsList]:
        self.render_modes.append(render_context.primary_mode)
        return Ok(self.artifact)


class FakeOutputEmitter:
    def __init__(self) -> None:
        self.cells: list[object] = []
        self.journal_records: list[JournalRecord] = []

    def emit_cell(self, cell: object) -> None:
        self.cells.append(cell)

    def emit_journal(self, record: JournalRecord) -> None:
        self.journal_records.append(record)
