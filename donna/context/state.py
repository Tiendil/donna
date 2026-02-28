from typing import TYPE_CHECKING

from donna.context.entity_cache import TimedCache, TimedCacheValue
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.machine import errors as machine_errors

if TYPE_CHECKING:
    from donna.machine.state import ConsistentState


class _StateCacheValue(TimedCacheValue):
    __slots__ = ("state", "state_json")

    def __init__(
        self,
        state: "ConsistentState",
        state_json: bytes,
        loaded_at_ms: int,
        checked_at_ms: int,
    ) -> None:
        super().__init__(loaded_at_ms=loaded_at_ms, checked_at_ms=checked_at_ms)
        self.state = state
        self.state_json = state_json


class StateCache(TimedCache):
    __slots__ = ("_session_state",)

    def __init__(self) -> None:
        self._session_state: _StateCacheValue | None = None

    @unwrap_to_error
    def load(self) -> Result["ConsistentState", ErrorsList]:
        from donna.machine.state import ConsistentState
        from donna.workspaces import utils as workspace_utils

        now_ms = self._now_ms()
        cached = self._session_state

        if cached is not None and self._is_within_lifetime(cached, now_ms):
            return Ok(cached.state)

        content = workspace_utils.session_world().unwrap().read_state("state.json").unwrap()
        if content is None:
            return Err([machine_errors.SessionStateNotInitialized()])

        if cached is not None and cached.state_json == content:
            self._mark_checked(cached, now_ms)
            return Ok(cached.state)

        state = ConsistentState.from_json(content.decode("utf-8"))
        self._session_state = _StateCacheValue(
            state=state,
            state_json=content,
            loaded_at_ms=now_ms,
            checked_at_ms=now_ms,
        )
        return Ok(state)

    @unwrap_to_error
    def save(self, state: "ConsistentState") -> Result[None, ErrorsList]:
        from donna.workspaces import utils as workspace_utils

        content = state.to_json().encode("utf-8")
        workspace_utils.session_world().unwrap().write_state("state.json", content).unwrap()
        now_ms = self._now_ms()
        self._session_state = _StateCacheValue(
            state=state,
            state_json=content,
            loaded_at_ms=now_ms,
            checked_at_ms=now_ms,
        )
        return Ok(None)
