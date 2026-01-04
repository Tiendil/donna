from typing import Annotated

import typer

from donna.domain.ids import create_id_parser
from donna.domain.types import ActionRequestId, RecordId

ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=create_id_parser(ActionRequestId), help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    ActionRequestId,
    typer.Option(parser=create_id_parser(ActionRequestId), help="The ID of the action request"),
]


RecordIdArgument = Annotated[
    RecordId,
    typer.Argument(parser=create_id_parser(RecordId), help="The ID of the record"),
]
