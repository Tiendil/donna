# Session Planning Guidelines

```toml donna
kind = "donna.artifacts.specification"
```

This document describes how Donna MUST plan work on a session with the help of workflows. The
document describes the process of planning, kinds of involved entities and requirements for them.

**This requirements MUST be applied to all planning workflows that Donna uses.**

## Overview

Donna's workflows create a plan of work on a session by iteratively polishing the set of session-level artifacts.

Artifacts are:

- `session.specification.work_scope` — a specification that describes the scope of work to be done on the session.
- `session.workflows.work_execution` — a workflow that describes the step-by-step plan of work to be done on the session.

The agent MUST create and iteratively polish these artifacts until they meet all quality criteria described in this document. After the plan is ready, the agent MUST run it as a workflow.

## Work Scope Specification

The work scope specification has a standard name `session.specification.work_scope` and describes the work to be done in the context of the current session.

The specification MUST contain the following sections:

1. `Developer request` — a copy of the original description of the work from the developer.
2. `Work description` — a high-level description of the work to be done, created by Donna
   based on the developer request.
3. `Goals` — a list of goals that work strives to achieve.
4. `Objectives` — a list of specific objectives that need to be completed to achieve the goals.
5. `Known constraints` — a list of constraints for the session.
6. `Acceptance criteria` — a list of acceptance criteria for the resulted work.
7. `Deliverables / Artifacts` — a list of concrete deliverables / artifacts that MUST be produced.

Sections `Developer request` and `Detailed work description` are free-form text sections.
Sections `Goals`, `Objectives` should contain lists of items.

### "Developer Request" section requirements

- This section MUST contain the original request from the developer. The request MUST NOT be modified by Donna.

### "Work Description" section requirements

- The section MUST contain a clear professional high-level description of the work to be done based
  on the developer's request.
- The section MUST be limited to a single paragraph with a few sentences.
- The sectino MUST explain what someone gains after these changes and how they can see it working.
  State the user-visible behavior the task will enable.

### "Goals" section requirements

- The section MUST contain a list of high-level goals that the work strives to achieve.

The goal quality criteria:

- A goal describes a desired end state, outcome or result.
- A goal defines what should ultimately be true, not how to achieve it.
- A goal must not be defined via listing cases, states, outcomes, etc. Instead, use one of the next
  approaches:
  a) summarize top-layer items into a single goal;
  b) split the goal into multiple more specific goals;
  c) reformulate to a list of second-layer items as required properties of the top-level goal.
- Each goal must has clear scope and boundaries.

### "Objectives" section requirements

- The section MUST contain a list of specific objectives that need to be completed to achieve the goals.

Objective quality criteria:

- An objective MUST describe an achieved state or capability not the act of describing it.
- An objective MUST be phrased as "X exists / is implemented / is defined / is executable /
  is enforced / …"
- An objective MUST be atomic: it MUST result in exactly one concrete deliverable: one artifact,
  one executable, one schema, one test suite, etc.
- An objective is a single clear, externally observable condition of the system (not a description,
  explanation, or analysis) that, when met, moves you closer to achieving a specific goal.
- An objective is a top-level unit of work whose completion results in a concrete artifact,
  behavior, or state change that can be independently verified without reading prose.
- Each goal MUST have a set of objectives that, when all achieved, ensure the goal is met.
- Each goal MUST have 2–6 objectives, unless the goal is demonstrably trivial (≤1 artifact, no dependencies).

### "Known Constraints" section requirements

- The section MUST contain a list of known constraints that the work MUST respect.

Constraint quality criteria:

- A known constraint describes a non-negotiable limitation or requirement that the work MUST
  respect (technical, organizational, legal, temporal, compatibility, security, operational).
- Each constraint MUST be derived from explicitly available inputs (the developer request, existed
  specifications, existed code, information provided by workflows). Donna MUST NOT invent
  constraints.
- Each constraint MUST be phrased as a verifiable rule using normative language: "MUST / MUST NOT /
  SHOULD / SHOULD NOT".
- Each constraint MUST be atomic: one rule per record (no "and/or" bundles). If multiple rules
  exist, split into multiple constraint records.
- Each constraint MUST be externally binding (something the plan must accommodate), not an
  internal preference.
- Constraints MUST NOT restate goals/objectives in different words. They are bounds, not outcomes.
- Constraints MUST NOT contain implementation steps, designs, or proposed solutions.
- Constraints MUST NOT include risks, unknowns, or speculative issues.
- Constraints MUST be written so a reviewer can answer true/false for compliance by inspecting
  artifacts, behavior, or configuration (not by reading explanatory prose).
- The section MAY be empty only if no constraints are explicitly known.

Examples:

- Good: `MUST remain compatible with Python 3.10`
- Good: `MUST not change public CLI flags`
- Good: `MUST avoid network access`
- Good: `MUST run on Windows + Linux`
- Bad: `We should do it cleanly`
- Bad: `Prefer elegant code`
- Bad: `Try to keep it simple`

### "Acceptance criteria" section requirements

- The section MUST contain a list of acceptance criteria that define how to evaluate the session's results.

Acceptance criteria quality criteria:

- An acceptance criterion describes a pass/fail condition that determines whether the session's
  results are acceptable to a reviewer, user, or automated gate.
- Each criterion MUST be derived from explicitly available inputs (developer request, previous
  sections of the plan). Donna MUST NOT invent new scope, features, constraints, or assumptions.
- Each criterion MUST be phrased as an externally observable, verifiable rule, using normative
  language ("MUST / MUST NOT / SHOULD / SHOULD NOT") or an equivalent test form such as
  Given/When/Then (Gherkin-style).
- Each criterion MUST be independently checkable by inspecting artifacts, running a command,
  executing tests, or observing runtime behavior/output — not by reading explanatory prose.
- Each criterion MUST be atomic: one condition per record (no "and/or" bundles). If multiple
  conditions exist, split into multiple criteria records.
- Criteria MUST NOT describe implementation steps, internal design decisions, or "how" to achieve the result.
- Criteria MUST NOT restate goals/objectives verbatim. Instead, they must state how success is
  demonstrated (e.g., observable behavior, produced files, enforced rules, test outcomes).

Coverage rules:

- Each objective MUST have ≥1 acceptance criterion that validates it.
- Each acceptance criterion MUST map to at least one objective (directly or via a goal that the objective serves).
- Where relevant, criteria SHOULD specify concrete evaluation conditions, such as:
  - exact CLI output/exit codes, produced artifacts and their locations;
  - supported platforms/versions, configuration prerequisites;
  - measurable thresholds (latency, memory, size limits), if such requirements are explicitly implied or stated.
  - etc.

Regression rules:

- If the developer request or known constraints imply preserving existing behavior, acceptance
  criteria SHOULD include explicit non-regression checks (what must remain unchanged).
- The section MUST NOT be empty.

### "Deliverables / Artifacts" section requirements

- The section MUST contain a list of concrete deliverables/artifacts that MUST be produced by the work.

Deliverable/artifact quality criteria:

- A deliverable/artifact record MUST name a concrete output that will exist after the work is
  complete (a file, module, package, binary, schema, configuration, test suite, generated report,
  published document, metric in the metrics storage, dashbord, etc.).
- Each deliverable/artifact MUST be derived from explicitly available inputs (developer request,
  prior sections of this plan). Donna MUST NOT invent new deliverables that introduce new scope.
- Each deliverable/artifact MUST be externally verifiable by inspecting the repository/workspace,
  produced files, or runtime outputs — not by reading explanatory prose.
- Each deliverable/artifact record MUST be phrased as an existence statement using normative
  language, e.g. "MUST include …", "MUST produce …", "MUST add …".
- Each deliverable/artifact record MUST be atomic: exactly one deliverable per record (no
  "and/or", no bundles). If multiple outputs are required, split into multiple records.
- Each deliverable/artifact MUST specify at least one of:
  - an exact path/location (preferred), or
  - an exact artifact identifier (module/package name, command name, schema name, etc.).
- If the deliverable is generated by running a command, the record SHOULD specify the command
  entrypoint (e.g., via a CLI (Command-Line Interface) command name) and the expected output
  location, without describing internal implementation steps.
- Deliverables MUST NOT be vague (e.g., "updated code", "better docs"). They MUST be concrete
  enough that a reviewer can confirm presence/absence.
- Deliverables MUST NOT restate goals, objectives, constraints, or acceptance criteria. They must
  list *outputs*, not outcomes or pass/fail checks.
- The section MUST NOT be empty.

Source files as artifacts:

- Explicitly add source files (paths) as deliverables/artifacts only if the task is specifically
  about creating or modifying those files (e.g., "MUST add docs/cli.md …").
- Do not add source files as deliverables/artifacts if they are unknown at planning time (i.e. we
  do not know which files will be changed/added). In such cases, focus on higher-level deliverables
  (e.g., "MUST add CLI documentation" instead of listing specific files).

## Work Execution Workflow

The work execution workflow has a standard name `session.workflows.work_execution` and describes the step-by-step plan of work to be done in the context of the current session.

The workflow MUST be an artifact of kind `workflow`, see details `{{ donna.directives.view("donna.specifications.default_text_artifacts_behavior") }}`. I.e. the final workflow must be a valid FSM that agent will execute with the help of `donna` tool.

Primary requirement:

1. **You MUST prefer non-linear or cyclic workflows for complex tasks instead of long linear sequences.** I.e. use loops, conditionals, parallel branches, etc. where appropriate. That should help you to apply changes iteratively, validate them early and often and to polish the results step by step. I.e. prefere an incremental/evolutionary approach over a big-bang one.
2. However, prefere multiple short loops over a single long loop. The approach `do everything then repeat from scratch` is a bad practice. Instead, break down the work into smaller steps that can be done, verified and polished independently.
3. The resulted workflow MUST ensure that there is at least 1 refine iteration will always be applied (for each loop).
4. Describe each operation with effort: add details, examples, behavior for edge cases, etc. Formulate each term and action precisely.

General requirements:

- Each workflow step should describe an operation dedicated to one semantically atomic task.
- Each operation of the workflow MUST be derived from explicitly available inputs (developer request +
  prior plan sections). It MUST NOT introduce new scope, features, constraints, or deliverables.
- Each workflow operation item MUST map to ≥1 objective.
- Each objective MUST be covered by ≥1 workflow operation that produces the required change/artifact,
  and where relevant by additional item(s) that validate it (tests, checks, demo run).
- Each workflow operation MUST be atomic: one primary action per item (no "and/or" bundles). If
  multiple actions are needed, split into multiple items.
- Each workflow operation MUST be actionable and specific enough that a agent can execute it
  without needing additional prose:
  - It SHOULD name the component/module/subsystem affected, if known.
  - It SHOULD name the concrete artifact(s) it will create/modify when those artifacts are already
    known from the "Deliverables / Artifacts" section (do not invent file paths).
- If a command is required (e.g., a CLI (Command-Line Interface) invocation, test runner command),
  operation SHOULD include the exact command.
- Workflow operation MUST NOT be vague (e.g., "Improve code quality", "Handle edge cases", "Do the thing").
- Workflow operations MUST respect all "Known constraints".
- If workflow operation includes research/design work, there results MUST be represented as concrete artifacts or changes in the `session.specification.work_scope` and `session.workflows.work_execution` artifacts.

Verification steps:

- The workflow SHOULD include explicit verification operations that demonstrate acceptance
  criteria, such as:
  - adding or updating automated tests;
  - running tests/lint/static checks (if such gates exist in the project inputs);
  - running a minimal end-to-end command or scenario that shows the user-visible behavior.
- Verification MUST be phrased as executable checks (commands, test suites, observable outputs), not
  as "Review the code" or "Make sure it works".

Examples:

- Good: "Implement the `foo` subcommand behavior to emit the required summary line for each generation."
- Good: "Add automated tests that assert the `foo` subcommand exit code and exact stdout lines for the sample fixture."
- Good: "Run `pytest -q` and confirm the new tests pass."
- Bad: "Implement feature and update tests and docs."
- Bad: "Consider performance implications."
- Bad: "Document the approach in detail."
