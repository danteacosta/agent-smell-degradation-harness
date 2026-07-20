.PHONY: test eval simulate gate analysis experiment mitigation dissertation all
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
mitigation:
	python -m eval.mitigation_report
dissertation:
	python -m eval.dissertation_bundle
all: test eval simulate gate
