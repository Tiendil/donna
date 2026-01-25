from typing import Annotated

import typer

from donna.domain.ids import ActionRequestId, ArtifactId, FullArtifactId, FullArtifactIdPattern, FullArtifactLocalId

ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=ActionRequestId, help="The ID of the action request"),
]


FullArtifactIdArgument = Annotated[
    FullArtifactId,
    typer.Argument(parser=FullArtifactId.parse, help="The full ID of the artifact"),
]


ArtifactPrefixArgument = Annotated[
    ArtifactId,
    typer.Argument(parser=ArtifactId, help="The artifact prefix to list/validate"),
]


FullArtifactIdPatternOption = Annotated[
    FullArtifactIdPattern | None,
    typer.Option(parser=FullArtifactIdPattern.parse, help="The full artifact pattern to list"),
]


FullArtifactLocalIdArgument = Annotated[
    FullArtifactLocalId,
    typer.Argument(parser=FullArtifactLocalId.parse, help="The full local ID of the artifact"),
]
