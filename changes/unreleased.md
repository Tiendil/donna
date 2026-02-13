
### Changes

- gh-35 Added workflow for creating Design documents.
  - Added `donna:rfs:work:design` workflow by analogy to `donna:rfc:work:request`.
  - Added instructions to use `donna:rfc:specs:design` and default output artifact `session:design:<short-problem-related-identifier>`.
  - Fixed typo in `donna:rfc:specs:design` (`guidlines` -> `guidelines`).
- gh-35 Renamed RFC request workflow id.
  - Renamed the RFC request workflow id to `donna:rfc:work:request`.
  - Updated references to point to `donna:rfc:work:request`.
- gh-35 Updated RFC orchestration to include design-first planning.
  - Added `design` step to `donna:rfc:work:do` between RFC creation and planning.
  - Updated `donna:rfc:work:plan` to use Design documents as the primary planning input, with RFC as optional helper context.
