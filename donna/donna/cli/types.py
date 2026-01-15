from typing import Annotated

import typer

from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactLocalId, NamespaceId

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


NamespaceIdArgument = Annotated[
    NamespaceId,
    typer.Argument(parser=NamespaceId, help="The ID of the namespace"),
]


FullArtifactLocalIdArgument = Annotated[
    FullArtifactLocalId,
    typer.Argument(parser=FullArtifactLocalId.parse, help="The full local ID of the artifact"),
]
