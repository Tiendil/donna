# Grooming Workflow

```toml donna
description = """
Initiate operations to groom and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc.
operation_id = "run_autoflake"
"""
```

Initiate operations to groom and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc.

## Run Autoflake

```toml donna
id = "run_autoflake"
kind = "action_request"

[[results]]
id = "completed"
description = "Autoflake has been run to remove unused imports and variables in the codebase."
next_operation_id = "run_isort"
```

1. Run `cd ./donna && poetry run autoflake .` to remove unused imports and variables in the codebase.
2. Mark this action request as completed.

## Run isort

```toml donna
id = "run_isort"
kind = "action_request"

[[results]]
id = "completed"
description = "isort has been run to sort imports in the codebase."
next_operation_id = "run_black"
```

1. Run `cd ./donna && poetry run isort .` to sort imports in the codebase.
2. Mark this action request as completed.

## Run Black

```toml donna
id = "run_black"
kind = "action_request"

[[results]]
id = "completed"
description = "Black has been run to format the codebase."
next_operation_id = "run_flake8"
```

1. Run `cd ./donna && poetry run black .` to format the codebase.
2. Mark this action request as completed.

## Run Flake8

```toml donna
id = "run_flake8"
kind = "action_request"

[[results]]
id = "completed"
description = "No linting errors found in the codebase."
next_operation_id = "run_mypy"

[[results]]
id = "repeat"
description = "Linting errors were fixed, need to check again."
next_operation_id = "run_flake8"
```

1. Run `cd ./donna && poetry run flake8 .` to check the codebase for style issues.
2. If any issues are found, fix them.
3. Repeat until no issues are found.
4. Mark this action request as completed.

Instructions on fixing special cases:

- `E800 Found commented out code` — remove the commented out code.
- `CCR001 Cognitive complexity is too high` — ignore by adding `# noqa: CCR001` at the end of the line.
- `F821 undefined name` when there are missing imports — add the necessary import statements at the top of the file.
- `F821 undefined name` in all other cases — ask the developer to fix it manually.

## Run Mypy

```toml donna
id = "run_mypy"
kind = "action_request"

[[results]]
id = "completed"
description = "No type checking errors found in the codebase."
next_operation_id = "finish"

[[results]]
id = "repeat"
description = "Type checking errors were fixed, need to check again."
next_operation_id = "run_mypy"
```

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

## Finish

```toml donna
id = "finish"
kind = "finish_workflow"

[[results]]
id = "completed"
description = "Grooming workflow is completed."
```
