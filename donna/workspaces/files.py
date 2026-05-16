from pathlib import Path
from stat import S_ISREG


class FileFingerprint:
    __slots__ = ("mtime_ns", "size")

    def __init__(self, *, mtime_ns: int, size: int) -> None:
        self.mtime_ns = mtime_ns
        self.size = size

    @classmethod
    def from_path(cls, path: Path) -> "FileFingerprint | None":
        try:
            file_stat = path.stat()
        except FileNotFoundError:
            return None

        if not S_ISREG(file_stat.st_mode):
            return None

        return cls(mtime_ns=file_stat.st_mtime_ns, size=file_stat.st_size)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileFingerprint):
            return NotImplemented

        return self.mtime_ns == other.mtime_ns and self.size == other.size
