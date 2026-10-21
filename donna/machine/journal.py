from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.protocol import JournalCell


def journal_cell(*, message: str, actor_id: str | None) -> JournalCell:
    """Capture the consistent task and active execution scope for one event."""
    # Task IDs are deliberately not caller-supplied: each work unit runs for the
    # task in the cached consistent state. Its mutable copy can already point to
    # another task while changes are being applied, but that task does not run
    # until the state is saved. Journal attribution must use that same snapshot.
    # If loading fails or no task is active, emit the event without a task ID.
    loaded_state = caches.get().state.load()
    task = loaded_state.unwrap().current_task if loaded_state.is_ok() else None

    # The machine scopes work-unit and operation IDs around their execution and
    # restores them on exit. Always read that scope so journal attribution agrees
    # with the active execution; caller-supplied IDs could contradict it. Outside
    # execution, the corresponding scoped IDs are None.
    execution = execution_context.get()

    return JournalCell(
        message=message,
        actor_id=actor_id,
        current_task_id=task.id if task is not None else None,
        current_work_unit_id=execution.current_work_unit_id,
        current_operation_id=execution.current_operation_id,
    )
