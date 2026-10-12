#!/usr/bin/env python3
"""Validate an existing public technical smoke; never issue model requests."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.antigravity_cli import validate_stream


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stream', type=Path, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--qualification-out', type=Path)
    args = parser.parse_args()
    if not args.model.startswith('gemini-'):
        parser.error('explicit Gemini slug required')
    raw = args.stream.read_text()
    try:
        _, usage = validate_stream(raw, args.model)
    except RuntimeError:
        print(json.dumps({'qualified': False, 'reason': 'tools, model mismatch or incomplete stream',
                          'research_collection_allowed': False}))
        return 2
    qualification = {'executable_sha256': hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                     'stream': raw}
    if args.qualification_out:
        # Raw technical stream contains local paths: keep the receipt private.
        import os
        fd = os.open(args.qualification_out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(qualification, stream)
    print(json.dumps({'qualified': True, 'usage': usage, 'confirmatory_eligible': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
