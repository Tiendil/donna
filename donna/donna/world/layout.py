import pathlib

from donna.core import utils
from donna.domain.types import RecordId, RecordKindId, StoryId

# TODO: Make configurable
DONNA_DIR_NAME = ".donna"


class Layout:

    def __init__(self, project: pathlib.Path, donna_dir: str) -> None:
        self.project = project
        self.donna = project / donna_dir
        self.config = self.donna / "config.toml"

        self.stories = self.donna / "stories"
        self.workflows = self.donna / "workflows"

    def story_dir(self, story_id: StoryId) -> pathlib.Path:
        return self.stories / story_id

    def story(self, story_id: StoryId) -> pathlib.Path:
        return self.story_dir(story_id) / "story.toml"

    def story_plan(self, story_id: StoryId) -> pathlib.Path:
        return self.story_dir(story_id) / "plan.toml"

    def story_log(self, story_id: StoryId) -> pathlib.Path:
        return self.story_dir(story_id) / "log.toml"

    def story_records_dir(self, story_id: StoryId) -> pathlib.Path:
        return self.story_dir(story_id) / "records"

    def story_records_index(self, story_id: StoryId) -> pathlib.Path:
        return self.story_records_dir(story_id) / "index.toml"

    def story_record_kind(self, story_id: StoryId, record_id: RecordId, kind: RecordKindId) -> pathlib.Path:
        return self.story_records_dir(story_id) / f"{record_id}-{kind}.toml"

    def next_story_number(self) -> int:
        existing_ids = [
            int(path.name.split("-")[0])
            for path in self.stories.iterdir()
            if path.is_dir() and path.name.split("-")[0].isdigit()
        ]
        next_id = max(existing_ids, default=0) + 1
        return next_id

    def sync(self) -> None:
        self.stories.mkdir(exist_ok=True)
        self.workflows.mkdir(exist_ok=True)

    def is_story_exists(self, story: StoryId) -> bool:
        return self.story_dir(story).exists()

    def create_donna_dir(self) -> None:
        self.donna.mkdir(exist_ok=True)
        self.sync()


_LAYOUT: Layout | None = None


def layout(
    project_dir: pathlib.Path | None = None,
    donna_dir: str = DONNA_DIR_NAME,
    create_donna_dir: bool = False,
) -> Layout:
    global _LAYOUT

    if _LAYOUT:
        if project_dir is not None or donna_dir != DONNA_DIR_NAME:
            raise NotImplementedError("Layout is already initialized with different parameters")

        return _LAYOUT

    if project_dir is None:
        project_dir = utils.project_dir(donna_dir)

    if project_dir is None:
        raise NotImplementedError("Could not determine project directory")

    _LAYOUT = Layout(project_dir, donna_dir)

    if create_donna_dir:
        _LAYOUT.create_donna_dir()

    _LAYOUT.sync()

    return _LAYOUT
