import importlib
import json
import pathlib

from click.testing import Result as CliResult
from typer.testing import CliRunner

from donna.cli.application import app

COMMAND_MODULES = (
    "donna.cli.commands.artifacts",
    "donna.cli.commands.sessions",
    "donna.cli.commands.skills",
    "donna.cli.commands.version",
    "donna.cli.commands.workspaces",
)


def load_cli_commands() -> None:
    for module_name in COMMAND_MODULES:
        importlib.import_module(module_name)


def make_runner() -> CliRunner:
    load_cli_commands()
    return CliRunner()


def invoke(args: list[str]) -> CliResult:
    return make_runner().invoke(app, args)


def json_lines(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.startswith("{")]


def write_config(project_dir: pathlib.Path, *, workflow_dirs: list[str] | None = None) -> pathlib.Path:
    workflow_dirs = workflow_dirs or ["workflows"]
    config_path = project_dir / "donna.toml"
    workflow_dirs_text = ", ".join(f'"{path}"' for path in workflow_dirs)
    config_path.write_text(f"version = 1\nworkflow_dirs = [{workflow_dirs_text}]\n", encoding="utf-8")
    return config_path


def write_workflow(
    project_dir: pathlib.Path,
    *,
    path: str = "workflows/test.donna.md",
    title: str = "Test Workflow",
    description: str = "Workflow description.",
) -> pathlib.Path:
    artifact_path = project_dir / path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        f"""# {title}

```toml donna
id = "workflow"
kind = "donna.lib.workflow"
start_operation_id = "finish"
```

{description}

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

Done.
""",
        encoding="utf-8",
    )
    return artifact_path
