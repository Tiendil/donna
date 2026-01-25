# Grooming Workflow

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "run_autoflake"
```

Initiate operations to groom and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc.

## Run Autoflake

```toml donna
id = "run_autoflake"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Run `cd ./donna && poetry run autoflake .` to remove unused imports and variables in the codebase.
2. `{{ donna.lib.goto("run_isort") }}`

## Run isort

```toml donna
id = "run_isort"
kind = "donna.lib.request_action"
```

1. Run `cd ./donna && poetry run isort .` to sort imports in the codebase.
2. `{{ donna.lib.goto("run_black") }}`

## Run Black

```toml donna
id = "run_black"
kind = "donna.lib.request_action"
```

1. Run `cd ./donna && poetry run black .` to format the codebase.
2. `{{ donna.lib.goto("run_flake8") }}`

## Run Flake8

```toml donna
id = "run_flake8"
kind = "donna.lib.request_action"
```

1. Run `cd ./donna && poetry run flake8 .` to check the codebase for style issues.
2. If any issues are found, fix them.
3. If you made changes, do `{{ donna.lib.goto("run_autoflake") }}`.
4. If no issues are found, do `{{ donna.lib.goto("run_mypy") }}`.

Instructions on fixing special cases:

- `E800 Found commented out code` — remove the commented out code.
- `CCR001 Cognitive complexity is too high` — ignore by adding `# noqa: CCR001` at the end of the line.
- `F821 undefined name` when there are missing imports — add the necessary import statements at the top of the file.
- `F821 undefined name` in all other cases — ask the developer to fix it manually.

## Run Mypy

```toml donna
id = "run_mypy"
kind = "donna.lib.request_action"
```

1. Run `cd ./donna && poetry run mypy ./donna` to check the codebase for type annotation issues.
2. If there are issues found that you can fix, fix them.
3. Ask developer to fix any remaining issues manually.
4. If you made changes, do `{{ donna.lib.goto("run_autoflake") }}`.
5. If no issues are found, do `{{ donna.lib.goto("finish") }}`.

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
- Adding or removing attributes to classes. If you need to do it, ask the developer to fix the problem manually.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```
