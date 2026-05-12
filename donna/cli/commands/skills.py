from typing import Annotated

import typer

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.protocol.cells import Cell
from donna.skills.entities import SkillDocument
from donna.skills.fixtures import load_skill_text


@app.command("skill", help="Print built-in Donna skill documentation.")
def skill(context: typer.Context, document: Annotated[SkillDocument, typer.Argument()] = SkillDocument.usage) -> None:
    with command_context(context, load_environment=False) as command:
        command.write_cells(
            [
                Cell.build_markdown(
                    kind="skill",
                    content=load_skill_text(document),
                    document=document.value,
                )
            ]
        )
