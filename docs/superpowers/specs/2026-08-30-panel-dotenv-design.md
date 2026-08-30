# Panel runner `.env` loading design

## Goal

Allow the private LLM panel runner to load API credentials from a local,
Git-ignored `.env` file so users do not need to export variables manually.

## Design

`scripts/run_llm_panel.py` will load `.env` from the repository root before
constructing `PanelRunConfig`. The loader will support the narrow forms needed
by the panel configuration: `KEY=VALUE`, optional `export ` prefixes, blank
lines, full-line comments, and single- or double-quoted values. A valid
assignment has optional horizontal whitespace, an optional exact `export`
prefix followed by whitespace, a variable name matching the runtime contract
`^[A-Z][A-Z0-9_]*$`, optional horizontal whitespace around `=`, and a value.
Empty values are valid. For unquoted values, whitespace followed by `#` starts
an inline comment; a `#` without preceding whitespace is data. Quoted values
may contain `#`, and only escaped matching quotes and backslashes are
supported. After a quoted value, only whitespace and an optional comment are
valid; unsupported escapes and other trailing text are malformed. Duplicate
assignments are rejected. Existing process environment variables take
precedence based on presence, including an inherited empty value.

The loader will not print values, include them in manifests, or alter tracked
configuration. It parses the whole file before applying any assignments, so a
later error cannot leave partial state. `.env` remains ignored by Git and
should be permission-restricted by the user. Missing `.env` is valid; an
unreadable `.env`, invalid UTF-8, malformed assignment, or invalid variable
name fails closed. Diagnostics identify only a safe variable name when one is
available, otherwise only the line number; raw lines and values are never
echoed.

## Failure behavior

- Missing `.env`: continue using the inherited environment.
- Unreadable, non-regular `.env` (including a directory), or invalid UTF-8:
  exit before provider calls.
- Missing required variable after loading: preserve the existing panel
  configuration error.
- Malformed `.env` line or invalid variable name: exit before provider calls.
- Provider calls and output schemas remain unchanged.

## Verification

- Unit tests cover loading, precedence including inherited empty values,
  quoting, comments, malformed lines, duplicate keys, invalid encoding, and
  missing-file behavior without asserting private implementation details.
- CLI behavior tests cover `.env` resolution, malformed input with zero
  provider calls, secret-free stdout/stderr, and unchanged provider
  request/output/manifest contracts.
- File-system tests cover unreadable and directory `.env` paths without
  leaking raw paths or values.
- Existing panel-runtime tests continue to pass.
- A dry smoke preflight confirms the runner can resolve the private config from
  `.env` without logging secret values; the real smoke run remains bounded to
  ten tasks per judge.
