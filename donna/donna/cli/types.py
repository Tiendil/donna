from typing import Annotated

import typer

from donna.domain.types import ActionRequestId, str_to_action_request_id

ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=str_to_action_request_id, help="The ID of the action request"),
]
ActionRequestIdOption = Annotated[
    ActionRequestId,
    typer.Option(parser=str_to_action_request_id, help="The ID of the action request"),
]
