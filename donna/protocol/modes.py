from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.errors import UnsupportedFormatterMode

from donna.protocol.journal_formatters.automation import Formatter as AutomationFormatter
from donna.protocol.journal_formatters.base import Formatter
from donna.protocol.journal_formatters.human import Formatter as HumanFormatter
from donna.protocol.journal_formatters.llm import Formatter as LLMFormatter


def get_journal_formatter(mode: Protocol) -> Formatter:
    match mode:
        case Protocol.human:
            return HumanFormatter()
        case Protocol.llm:
            return LLMFormatter()
        case Protocol.automation:
            return AutomationFormatter()
        case _:
            raise UnsupportedFormatterMode(details={"mode": mode})
