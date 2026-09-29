from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.output_cells import AutomationOutputCell, HumanOutputCell, LLMOutputCell
from llm_tool_cli.protocol.output_cells.base import OutputCell


def project(cell: LogicCell, protocol: Protocol) -> OutputCell:
    original = cell.model_dump()
    outputs = cell.render(protocol)
    assert len(outputs) == 1
    assert isinstance(
        outputs[0],
        {
            Protocol.human: HumanOutputCell,
            Protocol.llm: LLMOutputCell,
            Protocol.automation: AutomationOutputCell,
        }[protocol],
    )
    assert cell.model_dump() == original
    return outputs[0]
