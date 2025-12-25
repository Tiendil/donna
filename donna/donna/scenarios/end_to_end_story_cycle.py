import textwrap

from donna.artifacts.domain import ArtifactsIndex
from donna.domain.types import ArtifactId, EventId, OperationId, OperationResultId
from donna.stories.events import EventTemplate
from donna.workflows.operations import Export, FinishTask, OperationResult, RequestAction
from donna.workflows.tasks import Task

DEVELOPER_DESCRIPTION_ID = ArtifactId("story-description-from-developer.md")
AGENT_DESCRIPTION_ID = ArtifactId("story-description-from-agent.md")
BIG_PICTURE_DESCRIPTION_ID = ArtifactId("story-big-picture.md")
GOALS_ID = ArtifactId("story-goals.md")
OBJECTIVES_ID = ArtifactId("story-objectives.md")
DEFINITION_OF_DONE_ID = ArtifactId("story-definition-of-done.md")
RISKS_ID = ArtifactId("story-risks.md")
PLAN_ID = ArtifactId("story-development-plan.md")


class StoryCycleStep(RequestAction):
    requested_artifact_id: ArtifactId

    def context_partial_description(self, task: Task) -> str:
        artifacts = ArtifactsIndex.load(task.story_id)

        # TODO: move to parameters?
        # TODO: this code is usefull only on the first pass
        #       when the whole documents are ready, we can not use this anymore
        #       because it will provide too much information for the operations
        #       that should not have it
        parts = [
            ("Developer request", DEVELOPER_DESCRIPTION_ID),
            ("Detailed work description", AGENT_DESCRIPTION_ID),
            ("Big picture", BIG_PICTURE_DESCRIPTION_ID),
            ("Primary goals", GOALS_ID),
            ("Objectives", OBJECTIVES_ID),
            ("Definition of done", DEFINITION_OF_DONE_ID),
            ("Risks and challenges", RISKS_ID),
        ]

        specification = []

        for title, artifact_id in parts:
            if not artifacts.has(artifact_id):
                break

            specification.append(f"# {title}")
            specification.append("")
            artifact = artifacts.get_artifact(artifact_id)
            specification.append(artifact.content)
            specification.append("")

        return "\n".join(specification)

    def context_plan(self, task: Task) -> str:
        artifacts = ArtifactsIndex.load(task.story_id)

        if not artifacts.has(PLAN_ID):
            raise NotImplementedError("Plan artifact is not available yet. STOP any work and ask the developer for help.")

        artifact = artifacts.get_artifact(PLAN_ID)
        return artifact.content


start = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle"),
    export=Export(
        name="Describe the story",
        description="Create a detailed description of the story based on the developer's request.",
    ),
    trigger_on=[],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:developer_description_provided"))],
    requested_artifact_id=DEVELOPER_DESCRIPTION_ID,
    request_template=textwrap.dedent(
        """
        1. If the developer hasn't provided you a description of the work for this story, ask them to provide it.
        2. Add the description as an artifact `{scheme.requested_artifact_id}` to the story.
        3. Mark this action request as completed.
        """
    ),
)


create_detailed_description = StoryCycleStep(
    id=OperationId("donna:end_to_end_story_cycle:create_detailed_description"),
    trigger_on=[EventTemplate(id=start.result(OperationResultId("completed")).event_id, operation_id=None)],
    results=[OperationResult.completed(EventId("donna:end_to_end_story_cycle:agent_description_created"))],
    requested_artifact_id=AGENT_DESCRIPTION_ID,
    request_template=textwrap.dedent(
        """
    Here is the beginig of the story specification.

    ```
    {partial_description}
    ```

    You MUST produce a clear professional high-level description of the work to be done based on the developer's
    description.

    1. Explain in a few sentences what someone gains after these changes and how they can see it working. State the
       user-visible behavior you will enable.
    2. Add the description as an artifact `{scheme.requested_artifact_id}` to the story.
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
    requested_artifact_id=BIG_PICTURE_DESCRIPTION_ID,
    request_template=textwrap.dedent(
        """
    Here is the beginig of the story specification.

    ```
    {partial_description}
    ```

    You MUST now produce a big-picture high-level summary of the work to be done:

    1. Explain in a few sentences what behavior you will change in the codebase to achieve the goal.
    2. Add the description as an artifact `{scheme.requested_artifact_id}` to the story.
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
    requested_artifact_id=GOALS_ID,
    request_template=textwrap.dedent(
        """
    Here is the beginig of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the primary goals of this task.

    1. List goals that the task is trying to achieve.
    2. Add the list as an artifact `{scheme.requested_artifact_id}` to the story.
    3. Mark this action request as completed.
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
    requested_artifact_id=OBJECTIVES_ID,
    request_template=textwrap.dedent(
        """
    Here is the beginig of the story specification.

    ```
    {partial_description}
    ```

    You MUST list objectives that need to be achieved to complete each goal.

    1. List objectives that need to be achieved to complete each goal.
    2. Add the list as an artifact `{scheme.requested_artifact_id}` to the story.
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
    requested_artifact_id=DEFINITION_OF_DONE_ID,
    request_template=textwrap.dedent(
        """
    Here is the beginig of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the criteria that must be met for this task to be considered done.

    1. List the criteria that must be met for this task to be considered done.
    2. Add the list as an artifact `{scheme.requested_artifact_id}` to the story.
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
    requested_artifact_id=RISKS_ID,
    request_template=textwrap.dedent(
        """
    Here is the beginig of the story specification.

    ```
    {partial_description}
    ```

    You MUST list the potential risks and challenges that may arise during the implementation of this task.

    1. List potential risks and challenges that may arise during the implementation of this task.
    2. Add the list as an artifact `{scheme.requested_artifact_id}` to the story.
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
    requested_artifact_id=PLAN_ID,
    request_template=textwrap.dedent(
        """
    Here is the  story specification.

    ```
    {partial_description}
    ```

    You MUST create a detailed work plan for this task.

    1. Break down the work into manageable steps and outline the approach you will take to implement the task.
    2. Add the plan as an artifact `{scheme.requested_artifact_id}` to the story.
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
    requested_artifact_id=ArtifactId("no-artifact-here"),
    request_template=textwrap.dedent(
        """
    Here is the work plan for the story.

    ```
    {plan}
    ```

    You MUST thoroughly execute the plan step by step to finish the work.

    1. Follow the plan carefully and implement the necessary changes to complete the task.
    2. Mark this action request as completed when the work is done.
    """
    ),
)


finish = FinishTask(
    id=OperationId("donna:end_to_end_story_cycle:finish_story_loop"),
    results=[],
    trigger_on=[
        EventTemplate(
            id=plan_story_execution.result(OperationResultId("completed")).event_id,
            operation_id=None,
        )
    ],
)
