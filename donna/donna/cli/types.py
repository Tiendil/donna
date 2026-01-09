from typing import Annotated

import typer

from donna.domain import types
from donna.domain.ids import FullArtifactId, NamespaceId, create_internal_id_parser, create_nested_id_parser

ActionRequestIdArgument = Annotated[
    types.ActionRequestId,
    typer.Argument(parser=create_internal_id_parser(types.ActionRequestId), help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    types.ActionRequestId,
    typer.Option(parser=create_internal_id_parser(types.ActionRequestId), help="The ID of the action request"),
]


RecordIdArgument = Annotated[
    types.RecordId,
    typer.Argument(parser=create_internal_id_parser(types.RecordId), help="The ID of the record"),
]


SlugArgument = Annotated[
    types.Slug,
    typer.Argument(parser=types.slug_parser, help="The slug identifier"),
]


FullArtifactIdArgument = Annotated[
    FullArtifactId,
    typer.Argument(parser=FullArtifactId.parse, help="The full ID of the artifact"),
]


NamespaceIdArgument = Annotated[
    NamespaceId,
    typer.Argument(parser=NamespaceId, help="The ID of the namespace"),
]
