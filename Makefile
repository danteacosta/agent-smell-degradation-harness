.PHONY: test eval simulate gate analysis experiment mitigation dissertation all dry-run thesis-analysis
test:
	pytest -q
eval:
	python -m eval
simulate:
	python -m eval.simulate_regressions $(if $(MODE),--mode $(MODE),)
gate:
	python -m gates
analysis:
	python -m eval.analysis_report
experiment:
	python -m eval.experiment
dry-run:
	python -m eval.experiment --dry-run
thesis-analysis:
	python -m eval.thesis_analysis --episodes eval/last_run_episodes.jsonl
mitigation:
	python -m eval.mitigation_report
dissertation:
	python -m eval.dissertation_bundle
all: test eval simulate gate
