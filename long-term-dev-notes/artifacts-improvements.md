
# Artifacts improvements

1. We may want to separate artifact content from artifact metadata. In that case we may not need multiple artifact kinds in the terms of content. Instead we will just have unified operations on ArtifactIndex items + read/write operations on artifact content.

2. Possible kinds of artifacts we may want to implement:

- `markdown` — like text artifact, but with more controlable output?
- `template` — a.k.a. jinja2 template or smth like that, to automatically build complex texts from simpler artifacts.
- `code` — artifact that contains code snippets and can, for example, validate their syntax.
- `script` — executable code snippets
- `toml` / `json` / `yaml` — structured data artifacts with validation and maybe some querying capabilities.
- `table` — tabular data artifact with support for different formats (csv, excel, etc.) and maybe some querying capabilities. Maybe even more database/notion like, like Fibery tables.

3. For list and graph items we may want to specify their content types, e.g. list of markdown artifacts, graph of code artifacts, etc. However, this approach may be better suitable for the case of separating artifact content from metadata (see point 1).
