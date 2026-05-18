import pathlib

from pytest_mock import MockerFixture

from donna.domain.constants import STATE_FILE_NAME
from donna.domain.paths import RelativeProjectPath
from donna.workspaces import sessions
from donna.workspaces.config import Config
from donna.workspaces.files import FileFingerprint


def _patch_session_globals(mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
    mocker.patch("donna.workspaces.sessions.project_dir", return_value=tmp_path)
    mocker.patch(
        "donna.workspaces.sessions.config",
        return_value=Config(session_dir=RelativeProjectPath(pathlib.Path(".session/donna"))),
    )


class TestDir:
    def test_dir__creates_session_directory(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)

        session_dir = sessions.dir()

        assert session_dir == tmp_path / ".session" / "donna"
        assert session_dir.is_dir()


class TestPath:
    def test_returns_configured_session_path_without_creating_it(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)

        assert sessions._path() == tmp_path / ".session" / "donna"
        assert not sessions._path().exists()


class TestStatePath:
    def test_returns_state_file_path_under_session_dir(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)

        assert sessions._state_path() == tmp_path / ".session" / "donna" / STATE_FILE_NAME


class TestEnsureDir:
    def test_ensure_dir__creates_session_directory(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)

        sessions.ensure_dir()

        assert (tmp_path / ".session" / "donna").is_dir()


class TestResetDir:
    def test_reset_dir__removes_existing_content_and_recreates_directory(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)
        state_path = tmp_path / ".session" / "donna" / STATE_FILE_NAME
        state_path.parent.mkdir(parents=True)
        state_path.write_bytes(b"state")

        sessions.reset_dir()

        assert state_path.parent.is_dir()
        assert not state_path.exists()


class TestReadState:
    def test_read_state__returns_none_for_missing_state_file(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)

        assert sessions.read_state() is None

    def test_read_state__returns_state_bytes(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)
        sessions.write_state(b"state")

        assert sessions.read_state() == b"state"


class TestWriteState:
    def test_write_state__writes_state_bytes(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        _patch_session_globals(mocker, tmp_path)
        sessions.dir()

        sessions.write_state(b"state")

        assert (tmp_path / ".session" / "donna" / STATE_FILE_NAME).read_bytes() == b"state"


class TestStateFingerprint:
    def test_state_fingerprint__returns_none_for_missing_state_file(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)

        assert sessions.state_fingerprint() is None

    def test_state_fingerprint__returns_fingerprint_for_state_file(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        _patch_session_globals(mocker, tmp_path)
        sessions.write_state(b"state")

        assert sessions.state_fingerprint() == FileFingerprint.from_path(
            tmp_path / ".session" / "donna" / STATE_FILE_NAME
        )
