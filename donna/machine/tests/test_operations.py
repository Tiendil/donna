from donna.domain.ids import SectionId
from donna.machine.operations import FsmMode, OperationMeta


class TestOperationMeta:
    def test_cells_meta__serializes_fsm_mode_and_allowed_transitions(self) -> None:
        meta = OperationMeta(fsm_mode=FsmMode.final, allowed_transtions={SectionId("next"), SectionId("done")})

        cell_meta = meta.cells_meta()

        assert cell_meta["fsm_mode"] == "final"
        assert set(cell_meta["allowed_transtions"]) == {"next", "done"}
