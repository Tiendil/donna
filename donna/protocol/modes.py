from llm_tool_cli.protocol import Protocol

from donna.protocol.errors import UnsupportedFormatterMode
from donna.protocol.formatters.automation import Formatter as AutomationFormatter
from donna.protocol.formatters.base import Formatter
from donna.protocol.formatters.human import Formatter as HumanFormatter
from donna.protocol.formatters.llm import Formatter as LLMFormatter


def get_cell_formatter(mode: Protocol) -> Formatter:
    match mode:
        case Protocol.human:
            return HumanFormatter()
        case Protocol.llm:
            return LLMFormatter()
        case Protocol.automation:
            return AutomationFormatter()
        case _:
            raise UnsupportedFormatterMode(details={"mode": mode})
