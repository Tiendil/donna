import textwrap

from donna.agents.domain import ActionRequest
from donna.artifacts.domain import ArtifactsIndex
from donna.domain.types import ArtifactId
from donna.workflows.operations import FinishTask, RequestAction, Simple, Export, OperationResult as OR
from donna.stories.events import EventTemplate as ET


start = Simple(
    id="donna:grooming",
    export=Export(name="Groom the donna's code",
                  description="Initiate operations to groom and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc."),
    trigger_on=[],
    results=[OR.completed("donna:grooming:started")]
)


run_autoflake = RequestAction(
    id="donna:grooming:run_autoflake",
    trigger_on=[start.result("completed").event_id,
                "donna:grooming:flake8:errors_found_and_fixed",
                "donna:grooming:mypy:errors_found_and_fixed"],
    results=[OR.completed("donna:grooming:autoflake_applied")],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run autoflake .` to remove unused imports and variables in the codebase.
        2. Mark this action request as completed.
        """
    )
)


run_isort = RequestAction(
    id="donna:grooming:run_isort",
    trigger_on=[run_autoflake.result("completed").event_id],
    results=[OR.completed("donna:grooming:isort_applied")],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run isort .` to sort the imports in the codebase.
        2. Mark this action request as completed.
        """
    )
)


run_black = RequestAction(
    id="donna:grooming:run_black",
    trigger_on=[run_isort.result("completed").event_id],
    results=[OR.completed("donna:grooming:black_applied")],
    request_template=textwrap.dedent(
        """
        1. Run `cd ./donna && poetry run black .` to format the codebase.
        2. Mark this action request as completed.
        """
    )
)


run_flake8 = RequestAction(
    id="donna:grooming:run_flake8",
    trigger_on=[run_black.result("completed").event_id],
    results=[OR.completed("donna:grooming:flake8:no_errors_found"),
             OR(id="errors_found_and_fixed",
                description="Agent found style issues and fixed all of them.",
                event_id="donna:grooming:flake8:errors_found_and_fixed")],
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
    trigger_on=[run_flake8.result("completed").event_id],
    results=[OR.completed("donna:grooming:mypy:no_errors_found"),
             OR(id="errors_found_and_fixed",
                description="Agent found type issues and fixed all of them.",
                event_id="donna:grooming:mypy:errors_found_and_fixed")],
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
        """
    )
)


finish = FinishTask(
    id="donna:grooming:finish",
    results=[],
    trigger_on=[run_mypy.result("completed").event_id]
)
