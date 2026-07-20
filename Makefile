.PHONY: test eval simulate gate analysis experiment all
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
all: test eval simulate gate
