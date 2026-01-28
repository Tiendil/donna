from donna.core import errors as core_errors


class EnvironmentError(core_errors.EnvironmentError):
    """Base class for environment errors in donna.machine."""

    cell_kind: str = "machine_error"


class SessionStateNotInitialized(EnvironmentError):
    code: str = "donna.machine.session_state_not_initialized"
    message: str = "Session state is not initialized."
    ways_to_fix: list[str] = ["Run Donna session start to initialize session state."]
