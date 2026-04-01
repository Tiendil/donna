from donna.core.entities import BaseEntity
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces.templates import RenderMode


class ArtifactRenderContext(BaseEntity):
    primary_mode: RenderMode
    current_task: Task | None = None
    current_work_unit: WorkUnit | None = None


RENDER_CONTEXT_VIEW = ArtifactRenderContext(primary_mode=RenderMode.view)
