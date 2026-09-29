from typing import Annotated

import typer
from llm_tool_cli.protocol import cell_shortcuts

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.skills.entities import SkillDocument
from donna.skills.fixtures import load_skill_text


@app.command("skill", help="Print built-in Donna skill documentation.")
def skill(context: typer.Context, document: Annotated[SkillDocument, typer.Argument()] = SkillDocument.usage) -> None:
    with command_context(context, load_environment=False) as command:
        command.write_cells([cell_shortcuts.skill(document=document.value, content=load_skill_text(document))])
