import textwrap

from donna.machine.action_requests import ActionRequest
from donna.machine.records import RecordsIndex
from donna.domain.types import RecordId
from donna.primitives.operations import Finish, RequestAction
from donna.machine.operations import OperationResult as OR
from donna.machine.workflows import Workflow


run_autoflake = RequestAction(
    id="donna:grooming:run_autoflake",
    results=[OR.completed(lambda: run_isort.id)],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run autoflake .` to remove unused imports and variables in the codebase.
        2. Mark this action request as completed.
        """
    )
)



workflow_start = Workflow(
    id="donna:grooming",
    operation_id=run_autoflake.id,
    name="Groom the donna's code",
    description="Initiate operations to groom and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc.",
)


run_isort = RequestAction(
    id="donna:grooming:run_isort",
    results=[OR.completed(lambda: run_black.id)],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run isort .` to sort the imports in the codebase.
        2. Mark this action request as completed.
        """
    )
)


run_black = RequestAction(
    id="donna:grooming:run_black",
    results=[OR.completed(lambda: run_flake8.id)],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run black .` to format the codebase.
        2. Mark this action request as completed.
        """
    )
)


run_flake8 = RequestAction(
    id="donna:grooming:run_flake8",
    results=[OR.completed(lambda: run_mypy.id),
             OR(id="errors_found_and_fixed",
                description="Agent found style issues and fixed all of them.",
                operation_id_=lambda: run_autoflake.id)],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run flake8 .` to check the codebase for style issues.
        2. If any issues are found, fix them.
        3. Repeat until no issues are found.
        4. Mark this action request as completed.

        Instructions on fixing special cases:

        - `E800 Found commented out code` — remove the commented out code.
        - `CCR001 Cognitive complexity is too high` — ignore by adding `# noqa: CCR001` at the end of the line.
        - `F821 undefined name` when there are missing imports — add the necessary import statements at the top of the file.
        - `F821 undefined name` in all other cases — ask the developer to fix it manually.
        """
    )
)


run_mypy = RequestAction(
    id="donna:grooming:run_mypy",
    results=[OR.completed(lambda: finish.id),
             OR(id="errors_found_and_fixed",
                description="Agent found type issues and fixed all of them.",
                operation_id_=lambda: run_autoflake.id)],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run mypy ./donna` to check the codebase for type annotation issues.
        2. If there are issues found that you can fix, fix them.
        3. Ask developer to fix any remaining issues manually.
        4. Mark this action request as completed.

        Issues you are allowed to fix:

        - No type annotation in the code — add type annotations based on the code context.
        - Mismatched type annotations that are trivial to fix — fix them.
        - Type conversion issues when there are explicit type conversions functions implied in the code — fix them.
        - Type conversion issues when the data is received from external sources (like database) and the type is known to be correct.

        Instructions on fixing special cases:

        - "variable can be None" when None is not allowed — add `assert variable is not None` if that explicitly makes sense from the code flow.

        Changes you are not allowed to make:

        - Introducing new types.
        - Introducing new protocols.
        - Adding `type: ignore[import-untyped]`. If you need to use it, ask the developer to install the missing types first or to fix the issue manually.
        """
    )
)


finish = Finish(
    id="donna:grooming:finish",
    results=[],
)
