"""Build public synthetic judge requests or score responses offline; no API calls."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from label_plane.judge_controls import build_controls, score_controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("requests", "manifest", "score"))
    parser.add_argument("--responses", type=Path)
    parser.add_argument("--configuration", action="append", default=[])
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    if args.mode == "requests":
        for case in build_controls()["cases"]:
            print(json.dumps(case["request"], sort_keys=True))
    elif args.mode == "manifest":
        print(json.dumps(build_controls(), indent=2, sort_keys=True))
    else:
        if args.responses is None:
            parser.error("score requires --responses")
        rows = [json.loads(line) for line in args.responses.read_text().splitlines() if line.strip()]
        print(json.dumps(score_controls(rows, args.configuration, args.repetitions), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
