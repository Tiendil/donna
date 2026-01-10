import enum
import jinja2


class RenderMode(enum.Enum):
    """Modes for rendering artifacts.

    Donna could render artifacts for different purposes, for example:

    - to be displayed to the agent when Donna is used via CLI
    - TODO: to be displayed to the agent when Donna is used as an agent tool
    - TODO: to be displayed to the agent when Donna is used as an MCP server
    - to be used for analysis by Donna itself

    In each mode Donna can produce different outputs.

    For example, it can output CLI commands in CLI mode, tool specifications in tool mode,
    special markup in analyze mode, etc.
    """
    cli = "cli"
    analyze = "analyze"


_ENVIRONMENT = None


def env() -> jinja2.Environment:
    from donna.world.primitives_register import register

    global _ENVIRONMENT

    if _ENVIRONMENT is not None:
        return _ENVIRONMENT

    _ENVIRONMENT = jinja2.Environment(loader=None,
                                      # we render into markdown, not into HTML
                                      # i.e. before (possible) displaying in the browser,
                                      # the result of the jinja2 render will be rendered by markdown renderer
                                      # markdown renderer should take care of escaping
                                      autoescape=False,
                                      auto_reload=False,
                                      extensions=[
                                          "jinja2.ext.do",
                                          "jinja2.ext.loopcontrols",
                                          "jinja2.ext.debug"
                                      ]
                                      )

    for renderer in register().renderers.values():
        _ENVIRONMENT.globals[renderer.id] = renderer

    return _ENVIRONMENT
