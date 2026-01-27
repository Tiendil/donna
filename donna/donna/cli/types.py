from typing import Annotated

import typer

from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactIdPattern, FullArtifactSectionId

ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=ActionRequestId, help="The ID of the action request"),
]


FullArtifactIdArgument = Annotated[
    FullArtifactId,
    typer.Argument(parser=FullArtifactId.parse, help="The full ID of the artifact"),
]


FullArtifactIdPatternOption = Annotated[
    FullArtifactIdPattern | None,
    typer.Option(parser=FullArtifactIdPattern.parse, help="The full artifact pattern to list"),
]


FullArtifactSectionIdArgument = Annotated[
    FullArtifactSectionId,
    typer.Argument(parser=FullArtifactSectionId.parse, help="The full section ID of the artifact"),
]
