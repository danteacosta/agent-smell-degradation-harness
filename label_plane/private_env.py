"""Load a narrow, secret-safe private environment file."""

from __future__ import annotations

import os
import re
from collections.abc import MutableMapping
from pathlib import Path

_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


class PrivateEnvError(ValueError):
    """The private environment file is present but invalid."""


def _parse_value(value_text: str, *, line_number: int) -> str:
    leading_trimmed = value_text.lstrip(" \t")
    had_leading_whitespace = leading_trimmed != value_text
    if not leading_trimmed:
        return ""
    if leading_trimmed[0] not in {"'", '"'}:
        if had_leading_whitespace and leading_trimmed.startswith("#"):
            return ""
        comment = re.search(r"[ \t]+#", leading_trimmed)
        if comment is not None:
            leading_trimmed = leading_trimmed[: comment.start()]
        return leading_trimmed.rstrip(" \t")

    quote = leading_trimmed[0]
    parsed: list[str] = []
    index = 1
    while index < len(leading_trimmed):
        character = leading_trimmed[index]
        if character == quote:
            remainder = leading_trimmed[index + 1 :]
            stripped_remainder = remainder.strip(" \t")
            if stripped_remainder and not stripped_remainder.startswith("#"):
                raise PrivateEnvError(
                    f"invalid private environment value on line {line_number}"
                )
            return "".join(parsed)
        if character == "\\":
            index += 1
            if index >= len(leading_trimmed) or leading_trimmed[index] not in {quote, "\\"}:
                raise PrivateEnvError(
                    f"unsupported private environment escape on line {line_number}"
                )
            character = leading_trimmed[index]
        parsed.append(character)
        index += 1
    raise PrivateEnvError(f"unterminated private environment value on line {line_number}")


def load_private_env(
    path: str | Path,
    *,
    environ: MutableMapping[str, str] | None = None,
) -> None:
    """Load a private environment file without overriding inherited values."""

    env_path = Path(path)
    try:
        if not env_path.exists():
            return
        if not env_path.is_file():
            raise PrivateEnvError("private environment path must be a regular file")
        source = env_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise PrivateEnvError("private environment file must be valid UTF-8") from None
    except OSError:
        raise PrivateEnvError("private environment file could not be read") from None

    assignments: dict[str, str] = {}
    for line_number, raw_line in enumerate(source.splitlines(), 1):
        line = raw_line.strip(" \t")
        if not line or line.startswith("#"):
            continue
        if line.startswith("export") and len(line) > 6 and line[6].isspace():
            line = line[6:].lstrip()
        if "=" not in line:
            raise PrivateEnvError(f"invalid private environment assignment on line {line_number}")
        name, value = line.split("=", 1)
        name = name.strip()
        if not _ENV_NAME.fullmatch(name):
            raise PrivateEnvError(f"invalid private environment name on line {line_number}")
        if name in assignments:
            raise PrivateEnvError(f"duplicate private environment name {name} on line {line_number}")
        assignments[name] = _parse_value(value, line_number=line_number)

    target = os.environ if environ is None else environ
    for name, value in assignments.items():
        target.setdefault(name, value)


__all__ = ["PrivateEnvError", "load_private_env"]
