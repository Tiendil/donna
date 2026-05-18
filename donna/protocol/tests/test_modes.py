import pytest

from donna.protocol.errors import UnsupportedFormatterMode
from donna.protocol.formatters.automation import Formatter as AutomationFormatter
from donna.protocol.formatters.human import Formatter as HumanFormatter
from donna.protocol.formatters.llm import Formatter as LLMFormatter
from donna.protocol.modes import Mode, get_cell_formatter


class TestGetCellFormatter:
    @pytest.mark.parametrize(
        ("mode", "formatter_class"),
        (
            (Mode.human, HumanFormatter),
            (Mode.llm, LLMFormatter),
            (Mode.automation, AutomationFormatter),
        ),
    )
    def test_returns_formatter_for_supported_mode(self, mode: Mode, formatter_class: type[object]) -> None:
        assert isinstance(get_cell_formatter(mode), formatter_class)

    def test_unsupported_mode_raises_internal_error(self) -> None:
        with pytest.raises(UnsupportedFormatterMode) as error_info:
            get_cell_formatter("missing")  # type: ignore[arg-type]

        assert error_info.value.arguments == {"mode": "missing"}
