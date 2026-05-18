from donna.domain.ids import SectionId
from donna.machine.artifacts import ArtifactSection
from donna.machine.changes import ChangeAddWorkUnit
from donna.machine.errors import ArtifactSectionNotFound
from donna.machine.operations import FsmMode, OperationMeta
from donna.machine.tests import make as machine_make
from donna.primitives.artifacts.workflow import (
    FinalOperationHasTransitions,
    NoOutgoingTransitions,
    SectionIsNotAnOperation,
    StartOperationMissing,
    Workflow,
    WorkflowMeta,
    WorkflowSectionNotWorkflow,
    WrongStartOperation,
    find_workflow_sections,
)
from donna.primitives.tests import make


def workflow_section(meta: WorkflowMeta | None = None) -> ArtifactSection:
    return machine_make.artifact_section(
        id=make.section_id("workflow"),
        kind=make.primitive_kind("donna.primitives.artifacts.workflow.Workflow"),
        title="Workflow",
        primary=True,
        meta=meta or WorkflowMeta(start_operation_id=make.section_id("start")),
    )


def operation_section(
    *,
    id: SectionId,
    transitions: set[SectionId] | None = None,
    fsm_mode: FsmMode = FsmMode.normal,
) -> ArtifactSection:
    return machine_make.artifact_section(
        id=id,
        kind=make.primitive_kind("donna.primitives.sections.text.Text"),
        meta=OperationMeta(
            fsm_mode=fsm_mode,
            allowed_transitions=transitions or set(),
        ),
    )


class TestFindWorkflowSections:
    def test_follows_operation_transitions_once(self) -> None:
        artifact = machine_make.artifact(
            [
                operation_section(id=make.section_id("start"), transitions={make.section_id("next")}),
                operation_section(id=make.section_id("next"), transitions={make.section_id("start")}),
            ]
        )

        sections = find_workflow_sections(make.section_id("start"), artifact)

        assert sections == {make.section_id("start"), make.section_id("next")}

    def test_stops_at_missing_or_non_operation_sections(self) -> None:
        artifact = machine_make.artifact(
            [
                operation_section(
                    id=make.section_id("start"),
                    transitions={make.section_id("next"), make.section_id("other")},
                ),
                machine_make.artifact_section(
                    id=make.section_id("next"),
                    kind=make.primitive_kind("donna.primitives.sections.text.Text"),
                ),
            ]
        )

        sections = find_workflow_sections(make.section_id("start"), artifact)

        assert sections == {make.section_id("start"), make.section_id("next"), make.section_id("other")}


class TestWorkflowMeta:
    def test_cells_meta__serializes_explicit_start_operation(self) -> None:
        meta = WorkflowMeta(start_operation_id=make.section_id("start"))

        assert meta.cells_meta() == {"start_operation_id": "start"}

    def test_cells_meta__omits_missing_start_operation(self) -> None:
        meta = WorkflowMeta()

        assert meta.cells_meta() == {}


class TestWorkflow:
    def test_execute_section__adds_work_unit_for_resolved_start_operation(self) -> None:
        artifact = machine_make.artifact(
            [
                workflow_section(WorkflowMeta(start_operation_id=make.section_id("start"))),
                operation_section(id=make.section_id("start"), fsm_mode=FsmMode.final),
            ]
        )

        result = Workflow().execute_section(
            machine_make.task(),
            machine_make.work_unit(),
            artifact,
            make.section_id("workflow"),
        )

        assert result.is_ok()
        change = result.unwrap()[0]
        assert isinstance(change, ChangeAddWorkUnit)
        assert change.task_id == machine_make.TASK_ID
        assert change.operation_id == make.operation_id("start")

    def test_validate_section__accepts_connected_workflow_ending_in_final_operation(self) -> None:
        artifact = machine_make.artifact(
            [
                workflow_section(WorkflowMeta(start_operation_id=make.section_id("start"))),
                operation_section(id=make.section_id("start"), transitions={make.section_id("next")}),
                operation_section(id=make.section_id("next"), fsm_mode=FsmMode.final),
            ]
        )

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_ok()

    def test_validate_section__uses_first_tail_section_as_default_start_operation(self) -> None:
        artifact = machine_make.artifact(
            [
                workflow_section(WorkflowMeta()),
                operation_section(id=make.section_id("start"), fsm_mode=FsmMode.final),
            ]
        )

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_ok()

    def test_validate_section__rejects_non_workflow_section_meta(self) -> None:
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.section_id("workflow"),
                    kind=make.primitive_kind("donna.primitives.sections.text.Text"),
                    primary=True,
                )
            ]
        )

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], WorkflowSectionNotWorkflow)

    def test_validate_section__requires_start_operation_when_workflow_has_no_tail_sections(self) -> None:
        artifact = machine_make.artifact([workflow_section(WorkflowMeta())])

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], StartOperationMissing)

    def test_validate_section__reports_wrong_explicit_start_operation(self) -> None:
        artifact = machine_make.artifact([workflow_section(WorkflowMeta(start_operation_id=make.section_id("start")))])

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_err()
        errors = result.unwrap_err()
        assert isinstance(errors[0], ArtifactSectionNotFound)
        assert isinstance(errors[1], WrongStartOperation)

    def test_validate_section__reports_non_operation_workflow_section(self) -> None:
        artifact = machine_make.artifact(
            [
                workflow_section(WorkflowMeta(start_operation_id=make.section_id("start"))),
                operation_section(id=make.section_id("start"), transitions={make.section_id("next")}),
                machine_make.artifact_section(
                    id=make.section_id("next"),
                    kind=make.primitive_kind("donna.primitives.sections.text.Text"),
                ),
            ]
        )

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], SectionIsNotAnOperation)

    def test_validate_section__reports_invalid_transition_rules(self) -> None:
        artifact = machine_make.artifact(
            [
                workflow_section(WorkflowMeta(start_operation_id=make.section_id("start"))),
                operation_section(
                    id=make.section_id("start"),
                    transitions={make.section_id("next"), make.section_id("done")},
                ),
                operation_section(
                    id=make.section_id("next"),
                    transitions={make.section_id("done")},
                    fsm_mode=FsmMode.final,
                ),
                operation_section(id=make.section_id("done")),
            ]
        )

        result = Workflow().validate_section(artifact, make.section_id("workflow"))

        assert result.is_err()
        errors = result.unwrap_err()
        assert {type(error) for error in errors} == {FinalOperationHasTransitions, NoOutgoingTransitions}
