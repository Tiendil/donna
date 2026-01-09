import textwrap

if __name__ == "__main__":

    from donna.domain import types
    from donna.domain.types import OperationId, RecordKindId
    from donna.machine.operations import OperationResult as OR
    from donna.machine.records import RecordKindSpec, RecordsIndex
    from donna.machine.tasks import Task
    from donna.machine.workflows import Workflow
    from donna.primitives.operations.finish import Finish as FinishTask
    from donna.primitives.operations.request_action import RequestAction
    from donna.primitives.records.pure_text import PureText

    DEVELOPER_DESCRIPTION = RecordKindSpec(
        kind=RecordKindId(types.Slug("session_developer_description")),
    )
    WORK_DESSCRIPTION = RecordKindSpec(
        kind=RecordKindId(types.Slug("session_work_description")),
    )

    GOAL = RecordKindSpec(kind=RecordKindId(types.Slug("session_goal")))

    OBJECTIVE = RecordKindSpec(kind=RecordKindId(types.Slug("session_objective")))
    CONSTRAINT = RecordKindSpec(kind=RecordKindId(types.Slug("session_constraint")))
    ACCEPTANCE_CRITERIA = RecordKindSpec(kind=RecordKindId(types.Slug("session_acceptance_criteria")))
    DELIVERABLE = RecordKindSpec(kind=RecordKindId(types.Slug("session_deliverable")))

    PLAN_ITEM = RecordKindSpec(kind=RecordKindId(types.Slug("session_plan_item")))


    def _get_aggregated_text_content(  # noqa: CCR001
        index: RecordsIndex, kind_spec: RecordKindSpec, as_list: bool
    ) -> str | None:
        records = index.get_records_for_kind(kind_spec.kind)

        if not records:
            return None

        lines = []

        for record in records:
            kind_items = index.get_record_kind_items(record.id, [kind_spec.kind])

            for kind in kind_items:
                if kind is None:
                    continue

                if not isinstance(kind, PureText):
                    raise NotImplementedError(
                        f"Record kind item for record '{record.id}' and kind '{kind_spec.kind}' is not PureText"
                    )

                if as_list:
                    lines.append(f"[{record.id}] {kind.content}")
                    continue

                lines.extend([kind.content, ""])

        if lines[-1] == "":
            lines.pop()

        return "\n".join(lines)


    class SessionCycleStep(RequestAction):
        requested_kind_spec: RecordKindSpec | None

        def context_partial_description(self, task: Task) -> str:  # noqa: CCR001
            records = RecordsIndex.load()

            # TODO: move to parameters?
            # TODO: this code is usefull only on the first pass
            #       when the whole documents are ready, we can not use this anymore
            #       because it will provide too much information for the operations
            #       that should not have it
            parts = [
                ("Developer request", False, DEVELOPER_DESCRIPTION),
                ("Detailed work description", False, WORK_DESSCRIPTION),
                ("Goals", True, GOAL),
                ("Objectives", True, OBJECTIVE),
                ("Known Constraints", True, CONSTRAINT),
                ("Acceptance Criteria", True, ACCEPTANCE_CRITERIA),
                ("Deliverables / Artifacts", True, DELIVERABLE),
                ("Work Plan", True, PLAN_ITEM),
            ]

            specification = []

            for title, as_list, kind_spec in parts:
                if not records.get_records_for_kind(kind_spec.kind):
                    break

                specification.append(f"# {title}")
                specification.append("")

                content = _get_aggregated_text_content(records, kind_spec, as_list)

                if content is None:
                    break

                specification.append(content)
                specification.append("")

            with open("/home/tiendil/tmp/last_spec.md", "w", encoding="utf-8") as f:
                f.write("\n".join(specification))

            return "\n".join(specification)


    create_detailed_description: "SessionCycleStep"
    list_primary_goals: "SessionCycleStep"
    list_objectives: "SessionCycleStep"
    list_constraints: "SessionCycleStep"
    list_acceptance_criteria: "SessionCycleStep"
    list_deliverables: "SessionCycleStep"
    prepare_plan: "SessionCycleStep"
    execute_plan: "SessionCycleStep"
    groom_the_result: "SessionCycleStep"
    finish: FinishTask


    start = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle")),
        results=[OR.completed(lambda: create_detailed_description.id)],
        requested_kind_spec=DEVELOPER_DESCRIPTION,
        request_template=textwrap.dedent(
            """
            1. Read the specification `donna.specifications.planning` if you haven't done it yet.
            2. If the developer hasn't provided you a description of the work for this session, ask them to provide it.
            3. Add the description as `{scheme.requested_kind_spec.verbose}` to the session.
            4. Mark this action request as completed.
            """
        ),
    )


    workflow_start = Workflow(
        id=types.WorkflowId(types.NestedId("donna:end_to_end_cycle:start")),
        operation_id=start.id,
        name="End-to-end session processing",
        description="End-to-end session processing: from work description through planning to execution and grooming.",
    )


    create_detailed_description = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:create_detailed_description")),
        results=[OR.completed(lambda: list_primary_goals.id)],
        requested_kind_spec=WORK_DESSCRIPTION,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST produce a high-level description of the work to be done based on the developer's description.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. Add the description as `{scheme.requested_kind_spec.verbose}` to the session.
        3. Mark this action request as completed.
        """
        ),
    )

    list_primary_goals = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:list_primary_goals")),
        results=[OR.completed(lambda: list_objectives.id), OR.repeat(lambda: list_primary_goals.id)],
        requested_kind_spec=GOAL,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST list the goals of this session.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. If you can identify one more goal:
        2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the session;
        2.2. mark this action request as `repeat`.
        3. If you can not identify more goals, mark this action request as `completed`.
        """
        ),
    )

    list_objectives = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:list_objectives")),
        results=[OR.completed(lambda: list_constraints.id), OR.repeat(lambda: list_objectives.id)],
        requested_kind_spec=OBJECTIVE,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST list objectives that need to be achieved to complete each goal.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. If you can identify one more objective:
        2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the session;
        2.2. mark this action request as `repeat`.
        3. If you can not identify more objectives, mark this action request as `completed`.
        """
        ),
    )

    list_constraints = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:list_constraints")),
        results=[OR.completed(lambda: list_acceptance_criteria.id), OR.repeat(lambda: list_constraints.id)],
        requested_kind_spec=CONSTRAINT,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST list the known constraints for this session.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. If you can identify one more constraint:
        2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the session;
        2.2. mark this action request as `repeat`.
        3. If you can not identify more constraints, mark this action request as `completed`.
        """
        ),
    )

    list_acceptance_criteria = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:list_acceptance_criteria")),
        results=[OR.completed(lambda: list_deliverables.id), OR.repeat(lambda: list_acceptance_criteria.id)],
        requested_kind_spec=ACCEPTANCE_CRITERIA,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST list the acceptance criteria for this session.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. If you can identify one more acceptance criterion:
        2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the session;
        2.2. mark this action request as `repeat`.
        3. If you can not identify more acceptance criteria, mark this action request as `completed`.
        """
        ),
    )

    list_deliverables = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:list_deliverables")),
        results=[OR.completed(lambda: prepare_plan.id), OR.repeat(lambda: list_deliverables.id)],
        requested_kind_spec=DELIVERABLE,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST list the deliverables / artifacts for this session.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. If you can identify one more deliverable:
        2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the session;
        2.2. mark this action request as `repeat`.
        2. If you can not identify more deliverables, mark this action request as `completed`.
        """
        ),
    )

    prepare_plan = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:prepare_plan")),
        results=[OR.completed(lambda: execute_plan.id), OR.repeat(lambda: prepare_plan.id)],
        requested_kind_spec=PLAN_ITEM,
        request_template=textwrap.dedent(
            """
        Here is current state of the session specification.

        ```
        {partial_description}
        ```

        You MUST prepare a detailed work plan for this session.

        1. Read the specification `donna.specifications.planning` if you haven't done it yet.
        2. If you can identify one more plan item:
        2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the session;
        2.2. mark this action request as `repeat`.
        3. If you can not identify more plan items, mark this action request as `completed`.
        """
        ),
    )

    execute_plan = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:execute_plan")),
        results=[OR.completed(lambda: groom_the_result.id)],
        requested_kind_spec=None,
        request_template=textwrap.dedent(
            """
        Here is the work plan for the session.

        ```
        {partial_description}
        ```

        You MUST thoroughly execute the plan step by step to finish the work.

        1. Follow the plan carefully and implement the necessary changes to complete the session.
        2. Mark this action request as completed when the work is done.
        """
        ),
    )


    groom_the_result = SessionCycleStep(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:groom_the_result")),
        results=[OR.completed(lambda: finish.id)],
        requested_kind_spec=None,
        request_template=textwrap.dedent(
            """
        You have completed the work according to the plan.

        Run the grooming workflow to ensure that the result is polished, clean, and ready for review.
        """
        ),
    )


    finish = FinishTask(
        id=OperationId(types.NestedId("donna:end_to_end_cycle:finish_session_loop")),
        results=[],
    )
