import pathlib

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result

from donna.machine.artifacts import Artifact
from donna.machine.templates import RenderMode
from donna.workspaces.artifacts import ArtifactRenderContext


class FakeRawArtifact:
    def __init__(self, path: pathlib.Path, artifact: Artifact) -> None:
        self.path = path
        self.artifact = artifact
        self.render_modes: list[RenderMode] = []

    def render(
        self, artifact_id: object, render_context: ArtifactRenderContext
    ) -> Result[Artifact, EnvironmentErrors]:
        self.render_modes.append(render_context.primary_mode)
        return Ok(self.artifact)
