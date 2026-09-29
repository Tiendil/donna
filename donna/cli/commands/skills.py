from typing import Annotated

import typer
from llm_tool_cli.protocol.logic_cells import ContentCell

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.skills.entities import SkillDocument
from donna.skills.fixtures import load_skill_text


@app.command("skill", help="Print built-in Donna skill documentation.")
def skill(context: typer.Context, document: Annotated[SkillDocument, typer.Argument()] = SkillDocument.usage) -> None:
    with command_context(context, load_environment=False) as command:
        command.write_cells(
            [
                ContentCell(
                    kind="skill",
                    content=load_skill_text(document),
                    media_type="text/markdown",
                    meta={"document": document.value},
                )
            ]
        )
