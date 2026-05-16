from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.machine import errors as machine_errors

if TYPE_CHECKING:
    from donna.machine.state import ConsistentState
    from donna.workspaces.files import FileFingerprint


class _StateCacheValue:
    __slots__ = ("fingerprint", "state")

    def __init__(
        self,
        state: "ConsistentState",
        fingerprint: "FileFingerprint",
    ) -> None:
        self.state = state
        self.fingerprint = fingerprint


class StateCache:
    __slots__ = ("_session_state",)

    def __init__(self) -> None:
        self._session_state: _StateCacheValue | None = None

    @unwrap_to_error
    def load(self) -> Result["ConsistentState", ErrorsList]:
        from donna.machine.state import ConsistentState
        from donna.workspaces import sessions as workspace_sessions

        cached = self._session_state
        fingerprint = workspace_sessions.state_fingerprint()

        if cached is not None:
            if fingerprint != cached.fingerprint:
                return Err([machine_errors.SessionStateChangedExternally()])

            return Ok(cached.state)

        if fingerprint is None:
            return Err([machine_errors.SessionStateNotInitialized()])

        content = workspace_sessions.read_state()
        if content is None:
            return Err([machine_errors.SessionStateNotInitialized()])

        latest_fingerprint = workspace_sessions.state_fingerprint()
        if latest_fingerprint != fingerprint:
            return Err([machine_errors.SessionStateChangedExternally()])

        state = ConsistentState.from_json(content.decode("utf-8"))
        self._session_state = _StateCacheValue(
            state=state,
            fingerprint=fingerprint,
        )
        return Ok(state)

    @unwrap_to_error
    def save(self, state: "ConsistentState") -> Result[None, ErrorsList]:
        from donna.workspaces import sessions as workspace_sessions

        cached = self._session_state
        if cached is not None and workspace_sessions.state_fingerprint() != cached.fingerprint:
            return Err([machine_errors.SessionStateChangedExternally()])

        content = state.to_json().encode("utf-8")
        workspace_sessions.write_state(content)
        fingerprint = workspace_sessions.state_fingerprint()
        if fingerprint is None:
            return Err([machine_errors.SessionStateNotInitialized()])

        self._session_state = _StateCacheValue(
            state=state,
            fingerprint=fingerprint,
        )
        return Ok(None)
