from abc import ABC, abstractmethod

from donna.protocol.journal import JournalRecord


class Formatter(ABC):
    __slots__ = ()

    @abstractmethod
    def format_journal(self, record: JournalRecord) -> bytes: ...  # noqa: E704
