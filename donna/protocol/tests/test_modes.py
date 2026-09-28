import pytest
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.errors import UnsupportedFormatterMode

from donna.protocol.journal_formatters.automation import Formatter as AutomationFormatter
from donna.protocol.journal_formatters.human import Formatter as HumanFormatter
from donna.protocol.journal_formatters.llm import Formatter as LLMFormatter
from donna.protocol.modes import get_journal_formatter


class TestGetJournalFormatter:
    @pytest.mark.parametrize(
        ("mode", "formatter_class"),
        (
            (Protocol.human, HumanFormatter),
            (Protocol.llm, LLMFormatter),
            (Protocol.automation, AutomationFormatter),
        ),
    )
    def test_returns_formatter_for_supported_mode(self, mode: Protocol, formatter_class: type[object]) -> None:
        assert isinstance(get_journal_formatter(mode), formatter_class)

    def test_unsupported_mode_raises_internal_error(self) -> None:
        with pytest.raises(UnsupportedFormatterMode) as error_info:
            get_journal_formatter("missing")  # type: ignore[arg-type]

        assert error_info.value.details == {"mode": "missing"}
