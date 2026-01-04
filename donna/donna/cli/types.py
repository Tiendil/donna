from typing import Annotated

from donna.machine.counters import create_id_parser
from donna.domain.types import ActionRequestId

import typer


ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=create_id_parser(ActionRequestId), help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    ActionRequestId,
    typer.Option(parser=create_id_parser(ActionRequestId), help="The ID of the action request"),
]
