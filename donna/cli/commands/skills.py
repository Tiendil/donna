from typing import Annotated

import typer
from llm_tool_cli.protocol import cell_shortcuts
from llm_tool_cli.skills import load_skill_text

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.skills import SkillDocument


@app.command("skill", help="Print built-in Donna skill documentation.")
def skill(context: typer.Context, document: Annotated[SkillDocument, typer.Argument()] = SkillDocument.usage) -> None:
    with command_context(context, load_environment=False) as command:
        content = load_skill_text(package="donna.skills", document=document.value).unwrap()
        command.write_cells([cell_shortcuts.skill(document=document.value, content=content)])
