#!/usr/bin/env python3
"""Explicit public technical qualification; never starts a research collection."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.claude_cli import ClaudeCLIProvider
from agents.providers import ProviderRequest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--evidence-directory', required=True, type=Path)
    args = parser.parse_args()
    provider = ClaudeCLIProvider(executable=args.executable, model=args.model,
                                 evidence_directory=args.evidence_directory)
    answer = provider.complete(ProviderRequest('Return exactly SETUP_OK.', {}, 'technical', 'text'))
    qualified = answer.strip() == 'SETUP_OK'
    print(json.dumps({'technical_qualified': qualified, 'scientific_calls': 0,
                      **provider.last_call_metadata}, sort_keys=True))
    return 0 if qualified else 2


if __name__ == '__main__':
    raise SystemExit(main())
