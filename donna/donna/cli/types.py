from typing import Annotated

import typer

from donna.domain.types import ActionRequestId
from donna.machine.counters import create_id_parser

ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=create_id_parser(ActionRequestId), help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    ActionRequestId,
    typer.Option(parser=create_id_parser(ActionRequestId), help="The ID of the action request"),
]
