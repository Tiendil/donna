import textwrap

from donna.domain.types import EventId, OperationId, OperationResultId, RecordId, RecordIdTemplate, RecordKindId
from donna.machine.events import EventTemplate
from donna.machine.operations import OperationExport as Export
from donna.machine.operations import OperationResult
from donna.machine.records import RecordKindSpec, RecordsIndex
from donna.machine.tasks import Task
from donna.primitives.operations.finish import Finish as FinishTask
from donna.primitives.operations.request_action import RequestAction
from donna.primitives.records.pure_text import PureText

DEVELOPER_DESCRIPTION = RecordKindSpec(
    record_id=RecordIdTemplate("story-description-from-developer"),
    kind=RecordKindId("pure_text"),
)
AGENT_DESCRIPTION = RecordKindSpec(
    record_id=RecordIdTemplate("story-description-from-agent"),
    kind=RecordKindId("pure_text"),
)

GOAL = RecordKindSpec(record_id=RecordIdTemplate("story-goal-{uid}"), kind=RecordKindId("story_goal"))

OBJECTIVE = RecordKindSpec(record_id=RecordIdTemplate("story-objective-{uid}"), kind=RecordKindId("story_objective"))
CONSTRAINT = RecordKindSpec(
    record_id=RecordIdTemplate("story-constraint-{uid}"), kind=RecordKindId("story_constraint")
)
ACCEPTANCE_CRITERIA = RecordKindSpec(
    record_id=RecordIdTemplate("story-acceptance-criteria-{uid}"), kind=RecordKindId("story_acceptance_criteria")
)
DELIVERABLE = RecordKindSpec(
    record_id=RecordIdTemplate("story-deliverable-{uid}"), kind=RecordKindId("story_deliverable")
)

PLAN_ITEM = RecordKindSpec(record_id=RecordIdTemplate("story-plan-item-{uid}"), kind=RecordKindId("story_plan_item"))


def _record_id_from_spec(kind_spec: RecordKindSpec) -> RecordId:
    record_id = RecordId(kind_spec.record_id)

    if "{uid}" in record_id:
        raise NotImplementedError(f"Record id template '{record_id}' must be resolved before use")

    return record_id


def _get_text_content(records: RecordsIndex, record_id: RecordId, kind: RecordKindId) -> str | None:
    record = records.get_record(record_id)

    if record is None:
        return None

    record_kind_items = records.get_record_kind_items(record_id, [kind])

    if not record_kind_items:
        return None

    record_kind_item = record_kind_items[0]

    if record_kind_item is None:
        return None

    if not isinstance(record_kind_item, PureText):
        raise NotImplementedError(f"Record kind item for record '{record_id}' and kind '{kind}' is not PureText")

    return record_kind_item.content


def _get_aggregated_text_content(index: RecordsIndex, kind_spec: RecordKindSpec) -> str | None:  # noqa: CCR001
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
                    f"Record kind item for record '{kind_spec.record_id}' and kind '{kind_spec.kind}' is not PureText"
                )

            lines.append(f"[{record.id}] {kind.content}")

    return "\n".join(lines)


class StoryCycleStep(RequestAction):
    requested_kind_spec: RecordKindSpec | None

    def context_partial_description(self, task: Task) -> str:  # noqa: CCR001
        records = RecordsIndex.load(task.story_id)

        # TODO: move to parameters?
        # TODO: this code is usefull only on the first pass
        #       when the whole documents are ready, we can not use this anymore
        #       because it will provide too much information for the operations
        #       that should not have it
        parts = [
            ("Developer request", False, DEVELOPER_DESCRIPTION),
            ("Detailed work description", False, AGENT_DESCRIPTION),
            ("Goals", True, GOAL),
            ("Objectives", True, OBJECTIVE),
            ("Known Constraints", True, CONSTRAINT),
            ("Acceptance Criteria", True, ACCEPTANCE_CRITERIA),
            ("Deliverables / Artifacts", True, DELIVERABLE),
            ("Work Plan", True, PLAN_ITEM),
        ]

        specification = []

        for title, aggregate, kind_spec in parts:
            if aggregate:
                if not records.get_records_for_kind(kind_spec.kind):
                    break
            else:
                record_id = _record_id_from_spec(kind_spec)

                if not records.has_record_kind(record_id, kind_spec.kind):
                    break

            specification.append(f"# {title}")
            specification.append("")

            if not aggregate:
                content = _get_text_content(records, record_id, kind_spec.kind)
            else:
                content = _get_aggregated_text_content(records, kind_spec)

            if content is None:
                break

            specification.append(content)
            specification.append("")

        with open("/home/tiendil/tmp/last_spec.md", "w", encoding="utf-8") as f:
            f.write("\n".join(specification))

        return "\n".join(specification)


start = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle"),
    export=Export(
        name="Describe the story",
        description="Create a detailed description of the story based on the developer's request.",
    ),
    trigger_on=[],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:developer_description_provided"))],
    requested_kind_spec=DEVELOPER_DESCRIPTION,
    request_template=textwrap.dedent(
        """
        1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
        2. If the developer hasn't provided you a description of the work for this story, ask them to provide it.
        3. Add the description as `{scheme.requested_kind_spec.verbose}` to the story.
        4. Mark this action request as completed.
        """
    ),
)


create_detailed_description = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:create_detailed_description"),
    trigger_on=[EventTemplate(id=start.result(OperationResultId("completed")).event_id, operation_id=None)],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:agent_description_created"))],
    requested_kind_spec=AGENT_DESCRIPTION,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST produce a high-level description of the work to be done based on the developer's description.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. Add the description as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)

list_goals_next_iteration_event_id = EventId("donna:end_to_end_story_cycle:primary_goals_next_iteration")

list_primary_goals = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_primary_goals"),
    trigger_on=[
        EventTemplate(
            id=create_detailed_description.result(OperationResultId("completed")).event_id,
            operation_id=None,
        ),
        EventTemplate(id=list_goals_next_iteration_event_id, operation_id=None),
    ],
    results=[
        OperationResult.completed(EventId("donna:end_to_end_story_cycle:primary_goals_listed")),
        OperationResult.next_iteration(list_goals_next_iteration_event_id),
    ],
    requested_kind_spec=GOAL,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the goals of this story.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. If you can identify one more goal:
    2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the story;
    2.2. mark this action request as `next_iteration`.
    3. If you can not identify more goals, mark this action request as `completed`.
    """
    ),
)

list_objectives_next_iteration_event_id = EventId("donna:end_to_end_story_cycle:primary_objectives_next_iteration")

list_objectives = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_objectives"),
    trigger_on=[
        EventTemplate(
            id=list_primary_goals.result(OperationResultId("completed")).event_id,
            operation_id=None,
        ),
        EventTemplate(id=list_objectives_next_iteration_event_id, operation_id=None),
    ],
    results=[
        OperationResult.completed(EventId("donna:end_to_end_story_cycle:objectives_listed")),
        OperationResult.next_iteration(list_objectives_next_iteration_event_id),
    ],
    requested_kind_spec=OBJECTIVE,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST list objectives that need to be achieved to complete each goal.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. If you can identify one more objective:
    2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the story;
    2.2. mark this action request as `next_iteration`.
    3. If you can not identify more objectives, mark this action request as `completed`.
    """
    ),
)

list_contstraints_next_iteration_event_id = EventId("donna:end_to_end_story_cycle:definition_of_done_next_iteration")

list_constraints = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_constraints"),
    trigger_on=[
        EventTemplate(
            id=list_objectives.result(OperationResultId("completed")).event_id,
            operation_id=None,
        ),
        EventTemplate(id=list_contstraints_next_iteration_event_id, operation_id=None),
    ],
    results=[
        OperationResult.completed(EventId("donna:end_to_end_story_cycle:constraints_listed")),
        OperationResult.next_iteration(list_contstraints_next_iteration_event_id),
    ],
    requested_kind_spec=CONSTRAINT,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the known constraints for this story.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. If you can identify one more constraint:
    2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the story;
    2.2. mark this action request as `next_iteration`.
    3. If you can not identify more constraints, mark this action request as `completed`.
    """
    ),
)

list_acceptance_criteria_next_iteration_event_id = EventId(
    "donna:end_to_end_story_cycle:acceptance_criteria_next_iteration"
)

list_acceptance_criteria = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_acceptance_criteria"),
    trigger_on=[
        EventTemplate(
            id=list_constraints.result(OperationResultId("completed")).event_id,
            operation_id=None,
        ),
        EventTemplate(id=list_acceptance_criteria_next_iteration_event_id, operation_id=None),
    ],
    results=[
        OperationResult.completed(EventId("donna:end_to_end_story_cycle:acceptance_criteria_listed")),
        OperationResult.next_iteration(list_acceptance_criteria_next_iteration_event_id),
    ],
    requested_kind_spec=ACCEPTANCE_CRITERIA,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the acceptance criteria for this story.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. If you can identify one more acceptance criterion:
    2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the story;
    2.2. mark this action request as `next_iteration`.
    3. If you can not identify more acceptance criteria, mark this action request as `completed`.
    """
    ),
)

list_deliverables_next_iteration_event_id = EventId("donna:end_to_end_story_cycle:deliverables_next_iteration")

list_deliverables = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_deliverables"),
    trigger_on=[
        EventTemplate(
            id=list_acceptance_criteria.result(OperationResultId("completed")).event_id,
            operation_id=None,
        ),
        EventTemplate(id=list_deliverables_next_iteration_event_id, operation_id=None),
    ],
    results=[
        OperationResult.completed(EventId("donna:end_to_end_story_cycle:deliverables_listed")),
        OperationResult.next_iteration(list_deliverables_next_iteration_event_id),
    ],
    requested_kind_spec=DELIVERABLE,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the deliverables / artifacts for this story.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. If you can identify one more deliverable:
    2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the story;
    2.2. mark this action request as `next_iteration`.
    2. If you can not identify more deliverables, mark this action request as `completed`.
    """
    ),
)

prepare_story_plan_next_iteration_event_id = EventId("donna:end_to_end_story_cycle:prepare_story_plan_next_iteration")

prepare_story_plan = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:prepare_story_plan"),
    trigger_on=[
        EventTemplate(
            id=list_deliverables.result(OperationResultId("completed")).event_id,
            operation_id=None,
        ),
        EventTemplate(id=prepare_story_plan_next_iteration_event_id, operation_id=None),
    ],
    results=[
        OperationResult.completed(EventId("donna:end_to_end_story_cycle:story_plan_prepared")),
        OperationResult.next_iteration(prepare_story_plan_next_iteration_event_id),
    ],
    requested_kind_spec=PLAN_ITEM,
    request_template=textwrap.dedent(
        """
    Here is current state of the story specification.

    ```
    {partial_description}
    ```

    You MUST prepare a detailed work plan for this story.

    1. Read the specification `donna/workflows/story-planning` if you haven't done it yet.
    2. If you can identify one more plan item:
    2.1. add it as a `{scheme.requested_kind_spec.verbose}` to the story;
    2.2. mark this action request as `next_iteration`.
    3. If you can not identify more plan items, mark this action request as `completed`.
    """
    ),
)

execute_story_plan = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:execute_story_plan"),
    trigger_on=[
        EventTemplate(
            id=prepare_story_plan.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:story_plan_executed"))],
    requested_kind_spec=None,
    request_template=textwrap.dedent(
        """
    Here is the work plan for the story.

    ```
    {partial_description}
    ```

    You MUST thoroughly execute the plan step by step to finish the work.

    1. Follow the plan carefully and implement the necessary changes to complete the story.
    2. Mark this action request as completed when the work is done.
    """
    ),
)


groom_the_result = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:groom_the_result"),
    trigger_on=[
        EventTemplate(
            id=execute_story_plan.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:result_groomed"))],
    requested_kind_spec=None,
    request_template=textwrap.dedent(
        """
    You have completed the work according to the plan.

    Run the grooming workflow to ensure that the result is polished, clean, and ready for review.
    """
    ),
)


finish = FinishTask(
    id=OperationId("donna:end_to_end_story_cycle:finish_story_loop"),
    results=[],
    trigger_on=[
        EventTemplate(
            id=groom_the_result.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
)
