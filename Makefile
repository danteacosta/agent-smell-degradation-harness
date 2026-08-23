.PHONY: test eval simulate gate analysis experiment all dry-run thesis-analysis wedge-check prepilot freeze-candidate extension-clarification extension-dissertation

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

test:
	$(PYTHON) -m pytest -q
eval:
	$(PYTHON) -m eval
simulate:
	$(PYTHON) -m eval.simulate_regressions $(if $(MODE),--mode $(MODE),)
gate:
	$(PYTHON) -m gates
analysis:
	$(PYTHON) -m eval.analysis_report
experiment:
	$(PYTHON) -m eval.experiment
dry-run:
	$(PYTHON) -m eval.experiment --dry-run
thesis-analysis:
	$(PYTHON) -m eval.thesis_analysis --episodes eval/last_run_episodes.jsonl
prepilot:
	$(PYTHON) -m eval.prepilot
freeze-candidate:
	$(PYTHON) -m eval.freeze --status candidate
# Optional clarification experiments deliberately live outside the scientific
# pipeline.  They are never prerequisites for pre-pilot, pilot, or CI gates.
extension-clarification:
	$(PYTHON) -m eval.mitigation_report
extension-dissertation:
	$(PYTHON) -m eval.dissertation_bundle
wedge-check:
	$(PYTHON) -m pytest -q tests/test_wedge.py tests/test_wedge_acceptance.py
	$(PYTHON) -m wedge --fixture demo-clean
	@$(PYTHON) -m wedge --fixture demo-smelly; test $$? -ne 0
	@$(PYTHON) -m wedge --fixture demo-degraded; test $$? -ne 0
all: test eval simulate gate
