# Polishing Workflow

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "run_autoflake_script"
```

Initiate operations to polish and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc.

## Run Autoflake

```toml donna
id = "run_autoflake_script"
kind = "donna.lib.run_script"
fsm_mode = "start"
save_stdout_to = "autoflake_output"
goto_on_success = "run_isort_script"
goto_on_failure = "fix_autoflake"
```

```bash donna script
#!/usr/bin/env bash

autoflake ./donna
```

## Fix Autoflake Issues

```toml donna
id = "fix_autoflake"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("autoflake_output") }}
```

1. Fix the autoflake issues based on the output above.
2. Ensure your changes are saved.
3. `{{ donna.lib.goto("run_autoflake_script") }}`

## Run isort

```toml donna
id = "run_isort_script"
kind = "donna.lib.run_script"
save_stdout_to = "isort_output"
goto_on_success = "run_black_script"
goto_on_failure = "fix_isort"
```

```bash donna script
#!/usr/bin/env bash

isort ./donna
```

## Fix isort Issues

```toml donna
id = "fix_isort"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("isort_output") }}
```

1. Fix the isort issues based on the output above.
2. Ensure your changes are saved.
3. `{{ donna.lib.goto("run_autoflake_script") }}`

## Run Black

```toml donna
id = "run_black_script"
kind = "donna.lib.run_script"
save_stdout_to = "black_output"
goto_on_success = "run_flake8_script"
goto_on_failure = "fix_black"
```

```bash donna script
#!/usr/bin/env bash

black ./donna
```

## Fix Black Issues

```toml donna
id = "fix_black"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("black_output") }}
```

1. Fix the Black issues based on the output above.
2. Ensure your changes are saved.
3. `{{ donna.lib.goto("run_autoflake_script") }}`

## Run Flake8

```toml donna
id = "run_flake8_script"
kind = "donna.lib.run_script"
save_stdout_to = "flake8_output"
goto_on_success = "run_mypy_script"
goto_on_failure = "fix_flake8"
```

```bash donna script
#!/usr/bin/env bash

flake8 ./donna 2>&1
```

## Fix Flake8 Issues

```toml donna
id = "fix_flake8"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("flake8_output") }}
```

1. Fix the flake8 issues based on the output above.
2. Ensure your changes are saved.
3. `{{ donna.lib.goto("run_autoflake_script") }}`

Instructions on fixing special cases:

- `E800 Found commented out code` — remove the commented out code.
- `CCR001 Cognitive complexity is too high` — ignore by adding `# noqa: CCR001` at the end of the line.
- `F821 undefined name` when there are missing imports — add the necessary import statements at the top of the file.
- `F821 undefined name` in all other cases — ask the developer to fix it manually.

## Run Mypy

```toml donna
id = "run_mypy_script"
kind = "donna.lib.run_script"
save_stdout_to = "mypy_output"
goto_on_success = "finish"
goto_on_failure = "fix_mypy"
```

```bash donna script
#!/usr/bin/env bash

mypy ./donna
```

## Fix Mypy Issues

```toml donna
id = "fix_mypy"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("mypy_output") }}
```

1. Fix the mypy issues based on the output above that you are allowed to fix.
2. Ask the developer to fix any remaining issues manually.
3. Ensure your changes are saved.
4. `{{ donna.lib.goto("run_autoflake_script") }}`

Issues you are allowed to fix:

- No type annotation in the code — add type annotations based on the code context.
- Mismatched type annotations that are trivial to fix — fix them.
- Type conversion issues when there are explicit type conversions functions implied in the code — fix them.
- Type conversion issues when the data is received from external sources (like database) and the type is known to be correct.

Instructions on fixing special cases:

- "variable can be None" when None is not allowed — add `assert variable is not None` if that explicitly makes sense from the code flow.

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
