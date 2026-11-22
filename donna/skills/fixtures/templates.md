# `donna` Templates

Donna renders workflow Markdown with Jinja before it parses sections and transitions. Use templates to share instructions, generate operations from parameters, and reuse command snippets across workflows.

## Configure Template Lookup

Set `template_dirs` in `donna.toml`. Each directory is relative to the Donna project root, which is the directory containing the active configuration file.

```toml
version = 1
template_dirs = ["./templates/project", "./templates/shared"]
```

Jinja searches these directories in order and uses the first match. For example, `review/steps.jinja` can come from either directory. Includes inside a template use the same search order. Template files use UTF-8 and may have any extension.

Use a canonical `@/` path to select one file from the project root. For example, `@/templates/shared/review/steps.jinja` selects that exact file even when a project override exists. The file must be inside a configured template directory. These lookup rules apply to `include`, `import`, and `extends`.

## Include Shared Markdown

Use `include` when a workflow needs a fragment rendered at a particular location. The fragment can use the calling template's variables and Donna directives.

For a simple include of a known file, prefer its canonical `@/` path. This selects the same file regardless of template directory order.

```jinja
{% include "@/templates/shared/review/checklist.md" %}
```

For a checklist embedded in an operation, use body text or an H3 heading. An H2 starts a new Donna section. Put the include on its own line so the surrounding Markdown stays separate from the fragment.

For inserting file text with `donna.lib.include`, see `donna -p llm skill workflows`.

## Generate an Operation With a Macro

A Jinja macro renders text from arguments. A macro can emit a complete Donna operation, including its H2 heading, configuration, and instructions. The workflow supplies the operation ID and the local ID of its successor.

Save the macro in `templates/shared/review/steps.jinja`.

````jinja
{% macro request_review(id, title, next_id) %}
## {{ title }}

```toml donna
id = "{{ id }}"
kind = "donna.lib.request_action"
```

Review the current changes and summarize any issues.
When the review is complete, use `{{ donna.lib.goto(next_id) }}`.
{% endmacro %}
````

Save the calling workflow in `workflows/review.donna.md`.

````markdown
# Review a Change

```toml donna
start_operation_id = "review"
```

{% import "review/steps.jinja" as review with context %}

{{ review.request_review("review", "Review the current changes", "finish") }}

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

Report the review results.
````

`import` makes the library's macros available under a name such as `review`. To call one macro by name, use `{% from "review/steps.jinja" import request_review with context %}`. Use `with context` when an imported macro calls a Donna directive or reads caller variables. In this example, `goto` needs the calling workflow's identity and render mode.

Place calls that generate operations at the top Markdown level after the workflow's H1. Give each call a distinct ID. Keep generated headings, IDs, kinds, and transitions consistent across view, execute, and analysis renders. Use runtime values for operation text that can vary during execution.

## Organize Template Libraries

Group reusable templates by the workflows that use them. A review library can include operation macros and a checklist. A release library can define macros for recurring release sections.

```text
templates/
  project/
    review/checklist.md
  shared/
    review/checklist.md
    review/steps.jinja
    release/sections.jinja
    common/commands.jinja
```

Pass workflow-specific values such as IDs, transition targets, and file paths as arguments. Share short command snippets in a command library when several workflows use them. Keep substantial executable logic in project scripts so it can be run and tested directly.

For example, save a command macro in `templates/shared/common/commands.jinja`.

```jinja
{% macro diff_command(summary=false) -%}
git diff{% if summary %} --stat{% endif %}
{%- endmacro %}
```

This macro only uses its arguments, so a workflow can import it without bringing in the calling context.

```jinja
{% import "common/commands.jinja" as commands %}
Review the summary from `{{ commands.diff_command(summary=true) }}`.
```

## Override a Shared Template

A file in an earlier directory replaces a file with the same relative name in a later directory. An override of an imported macro library should provide the macro names and arguments the workflows call. It can import the shared library through its exact `@/` path to reuse individual macros.

Use Jinja blocks when an override needs to change part of an included fragment. Save the shared checklist in `templates/shared/review/checklist.md`.

```jinja
### Review checklist

{% block checks %}
- Confirm the requested behavior.
{% endblock %}
```

Save the override in `templates/project/review/checklist.md`.

```jinja
{% extends "@/templates/shared/review/checklist.md" %}

{% block checks %}
{{ super() }}
- Check that the change follows the project conventions.
{% endblock %}
```

Use a name relative to the template directories when a workflow should pick up the override.

```jinja
{% include "review/checklist.md" %}
```

Jinja selects the project checklist. The exact `@/` path in `extends` selects the shared base, and `super()` inserts its original checklist item.

## Preview and Validate

Preview the generated Markdown and validate the resulting workflow.

```bash
donna -p llm render @/workflows/review.donna.md --mode view
donna -p llm validate @/workflows/review.donna.md
```

Use `--mode analysis` with `render` to inspect the transition markers Donna reads during analysis. Read `donna -p llm skill workflows` for workflow structure and `donna -p llm skill configuration` for project settings.
