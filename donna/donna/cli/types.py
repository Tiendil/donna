from typing import Annotated

import typer

from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactIdPattern, FullArtifactLocalId

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


FullArtifactLocalIdArgument = Annotated[
    FullArtifactLocalId,
    typer.Argument(parser=FullArtifactLocalId.parse, help="The full local ID of the artifact"),
]
