from donna.core.entities import BaseEntity
from donna.domain.types import ActionRequestId, OperationId, Slug, StoryId
from donna.machine.cells import AgentMessage
from donna.machine.plans import Plan, get_plan
from donna.machine.records import RecordsIndex
from donna.machine.tasks import Task, WorkUnit
from donna.world.layout import layout


class Story(BaseEntity):
    id: StoryId

    @classmethod
    def load(cls, story_id: StoryId) -> "Story":
        return cls.from_toml(layout().story(story_id).read_text())

    def save(self) -> None:
        layout().story(self.id).write_text(self.to_toml())

    def cells(self) -> list[AgentMessage]:
        return [
            AgentMessage(
                story_id=self.id,
                task_id=None,
                work_unit_id=None,
                message=f"Story ID: {self.id}",
                action_request_id=None,
            )
        ]


def create_story(slug: Slug) -> Story:
    story_number = layout().next_story_number()

    # TODO: make configurable
    story_id = StoryId(f"{story_number:04d}-{slug}")

    story = Story(
        id=story_id,
    )

    plan = Plan.build(story_id)

    records_index = RecordsIndex(story_id=story_id, records=[])

    layout().story_dir(story_id).mkdir(parents=True, exist_ok=True)
    layout().story_records_dir(story_id).mkdir(parents=True, exist_ok=True)

    story.save()

    plan.save()

    records_index.save()

    return story


def start_workflow(story_id: StoryId, operation_id: OperationId) -> None:
    plan = get_plan(story_id)

    task = Task.build(story_id)
    start = WorkUnit.build(task.id, operation_id)

    plan.add_task(task, start)

    plan.save()


# TODO: very unoptimal, improve later
def find_action_request_story(request_id: ActionRequestId) -> StoryId:  # noqa: CCR001
    for story_dir in layout().stories.iterdir():
        if not story_dir.is_dir():
            continue

        story_id = StoryId(story_dir.name)

        plan = get_plan(story_id)

        for request in plan.action_requests:
            if request.id == request_id:
                return story_id

    raise NotImplementedError(f"Action request with id '{request_id}' not found in any story")
