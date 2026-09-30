from llm_tool_cli.cli.application import create_app
from llm_tool_cli.cli.commands.skills import register_skill_command
from llm_tool_cli.cli.commands.version import register_version_command
from llm_tool_cli.core import settings

from donna.skills import SkillDocument

app = create_app(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")
register_skill_command(app, package="donna.skills", documents=SkillDocument)
register_version_command(app, distribution="donna")


def main() -> None:
    settings.initialize(tool_label=settings.ToolLabel("DONNA"))

    from donna.cli.commands import artifacts  # noqa: F401
    from donna.cli.commands import sessions  # noqa: F401
    from donna.cli.commands import workspaces  # noqa: F401

    app()
