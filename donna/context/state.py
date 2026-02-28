from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.machine import errors as machine_errors

if TYPE_CHECKING:
    from donna.machine.state import ConsistentState


class StateCache:
    __slots__ = ("_session_state",)

    def __init__(self) -> None:
        self._session_state: ConsistentState | None = None

    @unwrap_to_error
    def load(self) -> Result["ConsistentState", ErrorsList]:
        from donna.machine.state import ConsistentState
        from donna.workspaces import utils as workspace_utils

        if self._session_state is not None:
            return Ok(self._session_state)

        content = workspace_utils.session_world().unwrap().read_state("state.json").unwrap()
        if content is None:
            return Err([machine_errors.SessionStateNotInitialized()])

        state = ConsistentState.from_json(content.decode("utf-8"))
        self._session_state = state
        return Ok(state)

    @unwrap_to_error
    def save(self, state: "ConsistentState") -> Result[None, ErrorsList]:
        from donna.workspaces import utils as workspace_utils

        workspace_utils.session_world().unwrap().write_state("state.json", state.to_json().encode("utf-8")).unwrap()
        self._session_state = state
        return Ok(None)
