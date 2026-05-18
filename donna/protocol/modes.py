import enum

from donna.protocol.errors import UnsupportedFormatterMode
from donna.protocol.formatters.automation import Formatter as AutomationFormatter
from donna.protocol.formatters.base import Formatter
from donna.protocol.formatters.human import Formatter as HumanFormatter
from donna.protocol.formatters.llm import Formatter as LLMFormatter


class Mode(enum.StrEnum):
    human = "human"
    llm = "llm"
    automation = "automation"


def get_cell_formatter(mode: Mode) -> Formatter:
    match mode:
        case Mode.human:
            return HumanFormatter()
        case Mode.llm:
            return LLMFormatter()
        case Mode.automation:
            return AutomationFormatter()
        case _:
            raise UnsupportedFormatterMode(mode=mode)
