# Polishing Workflow

Initiate operations to polish and refine the donna codebase: running & fixing tests, formatting code, fixing type annotations, etc. This workflow MUST NOT be used to introduce new logic into the project or refactor it — only to fix existing issues.

Polishing MUST preserve intended behavior and MUST NOT weaken checker configuration merely to hide findings.
Fixes SHOULD address the cause of a finding before adding a suppression.
Suppressions MUST address understood findings, use the smallest practical scope, and respect the applicable architecture.
Use the project development environment for all checks.
Changes requiring new behavior, architectural restructuring, or an uncertain domain decision need developer authorization unless already covered by the current task.

## Run Tach

```toml donna
id = "run_tach_script"
kind = "donna.lib.run_script"
fsm_mode = "start"
save_stdout_to = "tach_output"
goto_on_success = "run_autoflake_script"
goto_on_failure = "fix_tach"
```

```bash donna script
#!/usr/bin/env bash

./bin/dev.sh uv run tach check 2>&1
```

## Fix Tach Issues

```toml donna
id = "fix_tach"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("tach_output") }}
```

Align imports with the module ownership and dependency direction in `specs/architecture/modules_layout.md`.
Use an existing permitted dependency or public boundary; do not loosen Tach configuration merely to allow an import.
Do not move modules or create new boundaries unless architectural restructuring is already authorized.
Ask the developer when the correct dependency direction is unclear.

1. Fix the tach issues based on the output above that you are allowed to fix.
2. Ask the developer to fix any remaining issues manually.
3. Ensure your changes are saved.
4. `{{ donna.lib.goto("run_tach_script") }}`

## Run Autoflake

```toml donna
id = "run_autoflake_script"
kind = "donna.lib.run_script"
save_stdout_to = "autoflake_output"
goto_on_success = "run_isort_script"
goto_on_failure = "fix_autoflake"
```

```bash donna script
#!/usr/bin/env bash

./bin/dev.sh uv run autoflake ./donna
```

## Fix Autoflake Issues

```toml donna
id = "fix_autoflake"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("autoflake_output") }}
```

Mechanical cleanup MUST preserve required dynamic behavior, public re-exports, and initialization side effects.
Inspect the purpose of any removed symbol that may serve those roles before accepting its removal.
Imports retained for side effects SHOULD make their purpose explicit enough to survive cleanup.

1. Fix the autoflake issues based on the output above.
2. Ensure your changes are saved.
3. `{{ donna.lib.goto("run_tach_script") }}`

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

./bin/dev.sh uv run isort ./donna
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
3. `{{ donna.lib.goto("run_tach_script") }}`

## Run Black

```toml donna
id = "run_black_script"
kind = "donna.lib.run_script"
save_stdout_to = "black_output"
goto_on_success = "run_codespell_script"
goto_on_failure = "fix_black"
```

```bash donna script
#!/usr/bin/env bash

./bin/dev.sh uv run black ./donna
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
3. `{{ donna.lib.goto("run_tach_script") }}`

## Run Codespell

```toml donna
id = "run_codespell_script"
kind = "donna.lib.run_script"
save_stdout_to = "codespell_output"
goto_on_success = "run_flake8_script"
goto_on_failure = "fix_codespell"
```

```bash donna script
#!/usr/bin/env bash

./bin/dev.sh uv run codespell ./donna 2>&1
```

## Fix Codespell Issues

```toml donna
id = "fix_codespell"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("codespell_output") }}
```

1. Fix spelling when the intended word is clear; ask the developer about unresolved findings.
2. Ensure your changes are saved.
3. `{{ donna.lib.goto("run_tach_script") }}`

Do not change compatibility-sensitive values unless the surrounding contract permits the correction:

- external names.
- serialized values.
- fixture data.
- command output expectations.
- URLs.
- compatibility strings.

Intentional project terminology SHOULD use the configured spelling allowlist when available.

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

./bin/dev.sh uv run flake8 ./donna 2>&1
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
3. `{{ donna.lib.goto("run_tach_script") }}`

Instructions on fixing special cases:

- `E800 Found commented out code` — remove the commented-out code unless it is part of documented behavior, example text, or fixture data.
- `CCR001 Cognitive complexity is too high` — when the behavior is understood and the complexity is accepted for the current design, add a narrow `# noqa: CCR001`; otherwise report the finding without broad refactoring.
- `F821 undefined name` when there are missing imports — add the necessary import statements at the top of the file.
- `F821 undefined name` in all other cases — ask the developer to fix it manually.

Prefer clear, local fixes over broad refactoring.
Security findings MUST NOT be suppressed unless the reported behavior is intentional and its implications are understood; ask the developer when unclear.
For print-output findings, use the existing output or diagnostic mechanism; test fixes SHOULD follow the test's intent.

## Run Mypy

```toml donna
id = "run_mypy_script"
kind = "donna.lib.run_script"
save_stdout_to = "mypy_output"
goto_on_success = "run_tests_script"
goto_on_failure = "fix_mypy"
```

```bash donna script
#!/usr/bin/env bash

./bin/dev.sh uv run mypy ./donna
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
4. `{{ donna.lib.goto("run_tach_script") }}`

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

Follow the static typing suppression rules in `specs/architecture/entities.md`.
Do not invent domain behavior or architectural abstractions to satisfy the checker.

## Run Tests

```toml donna
id = "run_tests_script"
kind = "donna.lib.run_script"
save_stdout_to = "tests_output"
goto_on_success = "finish"
goto_on_failure = "fix_tests"
```

```bash donna script
#!/usr/bin/env bash

./bin/dev.sh uv run pytest donna -o cache_dir=/tmp/donna-pytest-cache 2>&1
```

## Fix Test Issues

```toml donna
id = "fix_tests"
kind = "donna.lib.request_action"
```

```
{{ donna.lib.task_variable("tests_output") }}
```

1. Fix the test failures based on the output above that you are allowed to fix.
2. Ask the developer to fix any remaining failures manually.
3. Ensure your changes are saved.
4. `{{ donna.lib.goto("run_tach_script") }}`

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

Polishing workflow completed. Report the checks performed, any unavailable checks, and unresolved findings with enough context for the developer to decide the next action.
