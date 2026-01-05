from typing import Annotated

import typer

from donna.domain.ids import create_id_parser
from donna.domain import types

ActionRequestIdArgument = Annotated[
    types.ActionRequestId,
    typer.Argument(parser=create_id_parser(types.ActionRequestId), help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    types.ActionRequestId,
    typer.Option(parser=create_id_parser(types.ActionRequestId), help="The ID of the action request"),
]


RecordIdArgument = Annotated[
    types.RecordId,
    typer.Argument(parser=create_id_parser(types.RecordId), help="The ID of the record"),
]


SlugArgument = Annotated[
    types.Slug,
    typer.Argument(parser=types.slug_parser, help="The slug identifier"),
]


StoryIdArgument = Annotated[
    types.StoryId,
    typer.Argument(parser=types.child_slug_parser(types.StoryId), help="The ID of the story"),
]
