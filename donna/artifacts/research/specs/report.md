# Format of the Research Report document

```toml donna
kind = "donna.lib.specification"
```

This document describes the format and structure of a Research Report document used by Donna workflows from `donna:research:*` namespace.

## Overview

Donna introduces a group of workflows located in `donna:research:*` namespace that organize the process of researching a problem, collecting information, analyzing it, synthesizing options, and producing a final solution.

Session-related research artifacts MUST be stored as `session:research:<short-problem-related-identifier>`, unless the developer or parent workflow specifies a different location. The `<short-problem-related-identifier>` MUST be unique within the session.

Agent (via workflows) creates that artifact and updates it iteratively as the research process goes on.

## Research report structure

The research report is a Donna artifact (check `{{ donna.lib.view("donna:usage:artifacts") }}`) with the next structure:

- **Primary section** -- title and short description of the research problem.
- **Original problem description** -- original problem statement from the developer or parent workflow.
- **Formalized problem description** -- formalized version of the problem statement.
- **Goals** -- list of goals the research should achieve.
- **Desired form of final solution** -- description of the expected form and constraints for the final solution.
- **Solution space** -- description of analysis axes and synthesis dimensions.
- **Information to collect** -- list of information required to research the problem.
- **Information sources** -- list of sources that can provide the required information.
- **Collected information** -- gathered information with source references.
- **Analysis** -- analysis of collected information along the specified axes.
- **Synthesized solutions** -- synthesized solution options along the specified dimensions.
- **Evaluation** -- evaluation of synthesized solutions against the goals.
- **Final solution** -- final solution in the desired form.

## General language and format

- You MUST follow [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt) for keywords like MUST, SHOULD, MAY, etc.
- You MUST follow `{{ donna.lib.view("donna:usage:artifacts") }}`.
- You MUST follow the structure specified in this document.

### List format

- If a section described as a list, it MUST contain only a single markdown list.
- Each list item MUST be concise and clear.
- Each list item SHOULD be atomic and focused on a single aspect.
- Reviewer MUST be able to tell if the list item statement is true or false by inspecting resulting artifacts and behavior.

Common approaches to improve list items:

- Split a single item with an enumeration into multiple items with single focus.
- Transform an abstract item into a concrete one by referencing specific artifacts, measurable criteria, verifiable conditions, etc.

### Trusted inputs

Some sections of the research report MUST be based on trusted inputs. Trusted inputs are:

- Original problem description from the developer or parent workflow.
- Statements from the research report itself.
- Existing project documentation, code, and artifacts.
- External standards when they define constraints or best practices for the project domain.
- Documentation of third-party libraries, frameworks, or tools when it describes constraints or best practices.
- Primary research sources (datasets, reports, official publications) used to collect the required information.

## `Primary` section

- Title MUST be concise and reflect the essence of the research problem.
- Description MUST provide a brief overview of the problem, its purpose, and why research is needed.

## `Original problem description` section

- This section MUST contain the original problem description from the developer or from the parent workflow.
- The problem description MUST NOT be modified by agents.

## `Formalized problem description` section

- The section MUST contain a clear professional high-level description of the problem based on the original description.
- The section MUST be limited to a single paragraph with a few sentences.
- The section MUST explain what someone gains after the problem is solved and how they can see it working.

## `Goals` section

- This section MUST contain a list of goals that the research should achieve.
- Each goal MUST be grounded in the formalized problem description.

Goal quality criteria:

- A goal MUST be a desired end state, outcome, or result.
- A goal MUST define what ultimately should be true, not how to achieve it.

Examples:

- Bad: `- Investigate database options.`
- Good: `- Identify a database option that meets the project's scalability requirements.`

## `Desired form of final solution` section

- The section MUST be grounded in the formalized problem description and the goals.
- The section MUST describe the expected form of the final solution (for example: recommendation, decision matrix, implementation plan, or specification).
- The section MUST specify any required structure, formatting, or constraints on the final solution.
- The section SHOULD be a short list or a short paragraph, whichever is clearer for the problem.

## `Solution space` section

- The section MUST describe the axes along which collected information will be analyzed and the dimensions along which solutions will be synthesized.
- The section MUST contain two subsections: **Analysis axes** and **Synthesis dimensions**.
- Each axis or dimension MUST be grounded in the goals or the formalized problem description.

### `Analysis axes` subsection

- The subsection MUST contain a list of analysis axes.
- Each axis MUST describe a single perspective or criterion used to analyze information.
- Each axis SHOULD be phrased so it is clear how to apply it to collected information.

### `Synthesis dimensions` subsection

- The subsection MUST contain a list of synthesis dimensions.
- Each dimension MUST describe a single perspective or criterion used to synthesize solution options.
- Each dimension SHOULD make the comparison between options easier.

## `Information to collect` section

- The section MUST contain a list of information items required to research the problem.
- Each item MUST be specific enough to be collected or verified from sources.
- Each item MUST be grounded in the formalized problem description or the goals.

## `Information sources` section

- The section MUST contain a list of sources that can provide the required information.
- Each source entry MUST include a short identifier and a brief description of the source.
- Each source entry SHOULD include access method, scope, and reliability notes if relevant.
- Each source MUST be relevant to at least one item from **Information to collect**.

## `Collected information` section

- The section MUST contain the collected information mapped to the items from **Information to collect**.
- Each collected information item MUST reference one or more source identifiers from **Information sources**.
- The section MUST make it clear which information items are satisfied and which are missing.
- If a required information item cannot be collected, the section MUST state that explicitly and explain why.

## `Analysis` section

- The section MUST analyze the collected information along the **Analysis axes**.
- The analysis MUST be organized so each axis can be reviewed independently.
- The analysis MUST clearly separate observed facts from inferences or assumptions.
- The analysis format MUST fit the **Desired form of final solution** and should make downstream synthesis straightforward.

## `Synthesized solutions` section

- The section MUST present synthesized solutions or options in a format consistent with the **Synthesis dimensions**.
- Each solution SHOULD reference the analysis items that justify it.
- The synthesis format MUST fit the **Desired form of final solution**.

## `Evaluation` section

- The section MUST evaluate each synthesized solution against the **Goals**.
- The evaluation MUST make trade-offs explicit and identify risks or uncertainties.
- The evaluation MUST result in a clear comparison between solutions.

## `Final solution` section

- The section MUST present the final solution in the form specified in **Desired form of final solution**.
- The final solution MUST be justified by the evaluation results.
- If the evaluation does not allow a confident final solution, the section MUST state the remaining uncertainties and what additional information would resolve them.
