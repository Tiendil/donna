import pathlib

import pytest
from llm_tool_cli.config.errors import Unreadable

from donna.protocol.formatters import Formatter
from donna.protocol.formatters.human import Formatter as HumanFormatter
from donna.protocol.formatters.llm import Formatter as LlmFormatter


class TestFormatter:
    @pytest.mark.parametrize("formatter", [HumanFormatter(), LlmFormatter()])
    def test_format_error__preserves_shared_message(self, formatter: Formatter) -> None:
        error = Unreadable(pathlib.Path("config.toml"), "permission denied")

        assert formatter.format_error(error) == b"config.toml: permission denied\n"
