from abc import abstractmethod

from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.output_cells import AutomationOutputCell, HumanOutputCell, LLMOutputCell
from llm_tool_cli.protocol.output_cells.base import OutputCell


class DonnaCell(LogicCell):
    """A domain result with the same payload in each output protocol."""

    def render_human(self) -> list[OutputCell]:
        return [self._render(HumanOutputCell)]

    def render_llm(self) -> list[OutputCell]:
        return [self._render(LLMOutputCell)]

    def render_automation(self) -> list[OutputCell]:
        return [self._render(AutomationOutputCell)]

    @abstractmethod
    def _render(self, cell_type: type[OutputCell]) -> OutputCell: ...  # noqa: E704
