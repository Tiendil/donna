import importlib.metadata

from llm_tool_cli.protocol import write_output

from donna.cli.application import app


@app.command(help="Print the current Donna package version.")
def version() -> None:
    write_output(importlib.metadata.version("donna") + "\n")
