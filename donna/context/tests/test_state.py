import pathlib

from pytest_mock import MockerFixture

from donna.context.state import StateCache
from donna.domain.constants import STATE_FILE_NAME
from donna.domain.paths import RelativeProjectPath
from donna.machine import errors as machine_errors
from donna.machine.tests import make as machine_make
from donna.workspaces import sessions as workspace_sessions
from donna.workspaces.config import Config


def _patch_session_globals(mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
    mocker.patch("donna.workspaces.sessions.project_dir", return_value=tmp_path)
    mocker.patch(
        "donna.workspaces.sessions.config",
        return_value=Config(session_dir=RelativeProjectPath(pathlib.Path(".session/donna"))),
    )


class TestStateCache:
    def test_load__reports_not_initialized_without_state_file(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)

        result = StateCache().load()

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], machine_errors.SessionStateNotInitialized)

    def test_load__reads_consistent_state_from_workspace(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)
        state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()
        workspace_sessions.write_state(state.to_json().encode("utf-8"))

        result = StateCache().load()

        assert result.is_ok()
        assert result.unwrap() == state

    def test_load__returns_cached_state_while_fingerprint_matches(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)
        state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()
        workspace_sessions.write_state(state.to_json().encode("utf-8"))
        cache = StateCache()
        assert cache.load().is_ok()
        read_state = mocker.patch("donna.workspaces.sessions.read_state")

        result = cache.load()

        assert result.is_ok()
        assert result.unwrap() == state
        read_state.assert_not_called()

    def test_load__reports_cached_state_changed_externally(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)
        state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()
        workspace_sessions.write_state(state.to_json().encode("utf-8"))
        cache = StateCache()
        assert cache.load().is_ok()
        (tmp_path / ".session" / "donna" / STATE_FILE_NAME).write_bytes(b"external change")

        result = cache.load()

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], machine_errors.SessionStateChangedExternally)

    def test_save__writes_state_and_updates_cache(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)
        state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()

        result = StateCache().save(state)

        assert result.is_ok()
        assert workspace_sessions.read_state() == state.to_json().encode("utf-8")

    def test_save__reports_cached_state_changed_externally(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)
        state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()
        cache = StateCache()
        assert cache.save(state).is_ok()
        (tmp_path / ".session" / "donna" / STATE_FILE_NAME).write_bytes(b"external change")

        result = cache.save(state)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], machine_errors.SessionStateChangedExternally)
