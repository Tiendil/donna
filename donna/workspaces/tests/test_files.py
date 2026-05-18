import pathlib

from donna.workspaces.files import FileFingerprint


class TestFileFingerprint:
    def test_from_path__returns_fingerprint_for_regular_file(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "file.txt"
        path.write_text("data", encoding="utf-8")

        fingerprint = FileFingerprint.from_path(path)

        assert fingerprint is not None
        assert fingerprint.size == 4
        assert fingerprint.mtime_ns == path.stat().st_mtime_ns

    def test_from_path__returns_none_for_missing_path_or_directory(self, tmp_path: pathlib.Path) -> None:
        assert FileFingerprint.from_path(tmp_path / "missing.txt") is None
        assert FileFingerprint.from_path(tmp_path) is None

    def test_eq__compares_mtime_and_size(self) -> None:
        assert FileFingerprint(mtime_ns=1, size=2) == FileFingerprint(mtime_ns=1, size=2)
        assert FileFingerprint(mtime_ns=1, size=2) != FileFingerprint(mtime_ns=2, size=2)
        assert FileFingerprint(mtime_ns=1, size=2) != object()
