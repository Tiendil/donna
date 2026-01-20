from typing import Annotated

import typer

from donna.domain.ids import ActionRequestId, ArtifactId, FullArtifactId, FullArtifactLocalId

ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=ActionRequestId, help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    ActionRequestId,
    typer.Option(parser=ActionRequestId, help="The ID of the action request"),
]


FullArtifactIdArgument = Annotated[
    FullArtifactId,
    typer.Argument(parser=FullArtifactId.parse, help="The full ID of the artifact"),
]


ArtifactPrefixArgument = Annotated[
    ArtifactId,
    typer.Argument(parser=ArtifactId, help="The artifact prefix to list/validate"),
]


FullArtifactLocalIdArgument = Annotated[
    FullArtifactLocalId,
    typer.Argument(parser=FullArtifactLocalId.parse, help="The full local ID of the artifact"),
]
