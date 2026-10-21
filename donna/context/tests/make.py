import pathlib

from llm_tool_cli.core.result import Ok, Result

from donna.context.artifacts import ArtifactsCache
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.machine import ArtifactRenderContext, Caches
from donna.machine.artifacts import Artifact
from donna.machine.templates import RenderMode


def caches() -> Caches:
    return Caches(artifacts=ArtifactsCache(), primitives=PrimitivesCache(), state=StateCache())


class FakeRawArtifact:
    def __init__(self, path: pathlib.Path, artifact: Artifact) -> None:
        self.path = path
        self.artifact = artifact
        self.render_modes: list[RenderMode] = []

    def render(self, artifact_id: object, render_context: ArtifactRenderContext) -> Result[Artifact]:
        self.render_modes.append(render_context.primary_mode)
        return Ok(self.artifact)
