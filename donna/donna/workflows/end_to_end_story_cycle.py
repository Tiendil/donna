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
BIG_PICTURE_DESCRIPTION = RecordKindSpec(
    record_id=RecordIdTemplate("story-big-picture"),
    kind=RecordKindId("pure_text"),
)
GOAL = RecordKindSpec(record_id=RecordIdTemplate("story-goal-{uid}"), kind=RecordKindId("story_goal"))

OBJECTIVES = RecordKindSpec(record_id=RecordIdTemplate("story-objectives"), kind=RecordKindId("pure_text"))
DEFINITION_OF_DONE = RecordKindSpec(
    record_id=RecordIdTemplate("story-definition-of-done"),
    kind=RecordKindId("pure_text"),
)
RISKS = RecordKindSpec(record_id=RecordIdTemplate("story-risks"), kind=RecordKindId("pure_text"))
PLAN = RecordKindSpec(record_id=RecordIdTemplate("story-development-plan"), kind=RecordKindId("pure_text"))


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
            ("Big picture", False, BIG_PICTURE_DESCRIPTION),
            ("Primary goals", True, GOAL),
            ("Objectives", False, OBJECTIVES),
            ("Definition of done", False, DEFINITION_OF_DONE),
            ("Risks and challenges", False, RISKS),
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

        return "\n".join(specification)

    def context_plan(self, task: Task) -> str | None:
        records = RecordsIndex.load(task.story_id)

        plan_record_id = _record_id_from_spec(PLAN)

        if not records.has_record(plan_record_id):
            return None

        return _get_text_content(records, plan_record_id, PLAN.kind)


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
        1. If the developer hasn't provided you a description of the work for this story, ask them to provide it.
        2. Add the description as `{scheme.requested_kind_spec.verbose}` to the story.
        3. Mark this action request as completed.
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
    Here is the beginning of the story specification.

    ```
    {partial_description}
    ```

    You MUST produce a clear professional high-level description of the work to be done based on the developer's
    description.

    1. Explain in a few sentences what someone gains after these changes and how they can see it working. State the
       user-visible workflow you will enable.
    2. Add the description as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)


describe_big_picture = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:describe_big_picture"),
    trigger_on=[
        EventTemplate(
            id=create_detailed_description.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:big_picture_described"))],
    requested_kind_spec=BIG_PICTURE_DESCRIPTION,
    request_template=textwrap.dedent(
        """
    Here is the beginning of the story specification.

    ```
    {partial_description}
    ```

    You MUST now produce a big-picture high-level summary of the work to be done:

    1. Explain in a few sentences what workflow you will change in the codebase to achieve the goal.
    2. Add the description as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)


list_primary_goals = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_primary_goals"),
    trigger_on=[
        EventTemplate(
            id=describe_big_picture.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:primary_goals_listed"))],
    requested_kind_spec=GOAL,
    request_template=textwrap.dedent(
        """
    Here is the beginning of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the primary goals of this story.

    1. Review the the story specification above.
    2. Review already listed goals.
    3. If you can identify one more goal, add it as a
       `{scheme.requested_kind_spec.verbose}` to the story. Go to the item 2.
    4. If you can not identify more goals, mark this action request as completed.
    """
    ),
)


list_objectives = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_objectives"),
    trigger_on=[
        EventTemplate(
            id=list_primary_goals.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:objectives_listed"))],
    requested_kind_spec=OBJECTIVES,
    request_template=textwrap.dedent(
        """
    Here is the beginning of the story specification.

    ```
    {partial_description}
    ```

    You MUST list objectives that need to be achieved to complete each goal.

    1. List objectives that need to be achieved to complete each goal.
    2. Add the list as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)


list_definition_of_done = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_definition_of_done"),
    trigger_on=[
        EventTemplate(
            id=list_objectives.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:definition_of_done_listed"))],
    requested_kind_spec=DEFINITION_OF_DONE,
    request_template=textwrap.dedent(
        """
    Here is the beginning of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the criteria that must be met for this story to be considered done.

    1. List the criteria that must be met for this story to be considered done.
    2. Add the list as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)

list_risks_and_challenges = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:list_risks_and_challenges"),
    trigger_on=[
        EventTemplate(
            id=list_definition_of_done.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:risks_and_challenges_listed"))],
    requested_kind_spec=RISKS,
    request_template=textwrap.dedent(
        """
    Here is the beginning of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the potential risks and challenges that may arise during the implementation of this story.

    1. List potential risks and challenges that may arise during the implementation of this story.
    2. Add the list as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)

plan_story_execution = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:plan_story_execution"),
    trigger_on=[
        EventTemplate(
            id=list_risks_and_challenges.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:story_execution_planned"))],
    requested_kind_spec=PLAN,
    request_template=textwrap.dedent(
        """
    Here is the  story specification.

    ```
    {partial_description}
    ```

    You MUST create a detailed work plan for this story.

    1. Break down the work into manageable steps and outline the approach you will take to implement the story.
    2. Add the plan as `{scheme.requested_kind_spec.verbose}` to the story.
    3. Mark this action request as completed.
    """
    ),
)

execute_story_plan = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:execute_story_plan"),
    trigger_on=[
        EventTemplate(
            id=plan_story_execution.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:story_plan_executed"))],
    requested_kind_spec=None,
    request_template=textwrap.dedent(
        """
    Here is the work plan for the story.

    ```
    {plan}
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
