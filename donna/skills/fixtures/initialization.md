# `donna` Initialization

`donna init` creates a starter `donna.toml` for a project that does not have one yet.

The generated file is intentionally small. It gives the project a valid schema version, a session directory, workflow discovery directories, and commented examples for optional defaults and journal forwarding.

Use this document when a configuration file is missing, when adding Donna to a new project, or when checking what initialization should create.

For configuration syntax details, use:

```bash
donna -p llm skill configuration
```

For command usage after initialization, use:

```bash
donna -p llm skill usage
```

## Project Root

Run initialization from the directory that should contain `donna.toml`.

Without `--root`, `donna init` creates `donna.toml` in the current working directory. With `--root PATH`, it creates `donna.toml` in that existing directory and treats it as the project root for later commands.

The project root matters because Donna discovers it by locating `donna.toml`. `session_dir` and `workflow_dirs` are relative to that directory, and Donna reports workflow artifacts as `@/<relative-path>` anchored at that directory. Relative artifact paths passed to commands are resolved from the command's current working directory and accepted only when they point inside the project root.

## Create The Starter File

Create `donna.toml` in the current directory:

```bash
donna -p llm init
```

Create it in an explicit project root:

```bash
donna -p llm --root /path/to/project init
```

`init` does not overwrite an existing file.

Right after creating the starter file, check whether the default workflow discovery directories match the project layout. Ask the developer before changing project structure or introducing new workflow directories.

## Filling The Configuration

Start from the smallest configuration that matches the project.

General workflow:

1. Check whether the project already has workflow files.
2. Keep `session_dir` unchanged unless the project has an established runtime-state or temporary files location.
3. Keep `workflow_dirs` unchanged when project workflows live in `./workflows` or temporary workflows should live in `./.session/donna`.
4. Add or narrow `workflow_dirs` only when the real workflow layout requires it.
5. Configure `journal.cmd` only when project instructions provide a reliable journal command.

Do not create workflow files or new project directories during initialization unless the developer explicitly asks for that. `donna init` only creates `donna.toml`; runtime commands create the session directory lazily.

## First Workflow Files

Donna discovers Markdown workflow files ending with `.donna.md` under configured workflow directories.

After initialization, offer the developer to create the first project workflows automatically. Base the proposal on the project configuration, existing scripts, package manifests, CI definitions, test commands, formatter and linter commands, changelog or release files, and specifications or documentation templates.

Good starter workflows:

1. Polish code by running autoformatters and linters in order, capturing command output, asking the agent to fix issues, and looping until the code is clean.
2. Run tests, ask the agent to fix failures, and loop until all configured test suites pass.
3. Analyze branch changes and update the changelog or release notes.
4. Prepare a project-specific documentation or specification artifact from an existing template, then review it against its specification until it is complete.
5. Reproduce the project's CI pipeline locally by running the same checks in a deterministic order and routing failures to focused agent repair steps.
6. Verify changed deliverables against a specification, design document, or acceptance criteria, then route missing or incorrect deliverables back to fix steps.
7. Prepare implementation plans from existing RFC, design, issue, or specification documents and save the resulting workflow as a session artifact.
8. Run dependency, generated-file, schema, migration, or documentation-build checks when the project already has stable commands for them.

Use direct file edits to create or change workflow files. Donna commands inspect, validate, render, and run workflow artifacts; they do not edit project-owned workflow files for you.

Before adding or changing workflows, use:

```bash
donna -p llm skill workflows
```

## Validation Loop

After creating or editing `donna.toml`, verify that Donna can load the project config and initialize session state:

```bash
donna -p llm status
```

`status` is the right first check because a newly initialized project may have no workflow files yet.

If the project already has workflows, or if you created workflows during initialization, list visible workflows:

```bash
donna -p llm list
```

Then validate the discovered workflow artifacts:

```bash
donna -p llm validate --all
```

If `list` returns no workflows, that can be valid for a newly initialized project. Check `workflow_dirs`, directory existence, and `.donna.md` suffixes only when workflows were expected. When configuration loading fails, fix `donna.toml` before continuing with workflow work. When validation fails, fix the workflow source files before running them.
