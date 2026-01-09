import pathlib

from donna.core import utils
from donna.domain.types import RecordId, RecordKindId
from donna.world.config import config

# TODO: Make configurable
DONNA_DIR_NAME = ".donna"


class Layout:

    def __init__(self, project: pathlib.Path, donna_dir: str) -> None:
        self.project = project
        self.donna = project / donna_dir

        self.workflows = self.donna / "workflows"

        # TODO: this is incorrect code, we should use worlds from configs
        self.session = config().get_world("session").path

    def session_plan(self) -> pathlib.Path:
        return self.session / "plan.json"

    def session_records_dir(self) -> pathlib.Path:
        return self.session / "records"

    def session_records_index(self) -> pathlib.Path:
        return self.session / "index.json"

    def session_record_kind(self, record_id: RecordId, kind: RecordKindId) -> pathlib.Path:
        return self.session / f"{record_id}.{kind}.json"

    def session_counters(self) -> pathlib.Path:
        return self.session_counters / "counters.json"

    def sync(self) -> None:
        self.session.mkdir(exist_ok=True)
        self.workflows.mkdir(exist_ok=True)

    def create_donna_dir(self) -> None:
        # TODO: this is incorrect code, we should use worlds from configs
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
