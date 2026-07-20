.PHONY: test eval simulate gate experiment all
test:
	pytest -q
eval:
	python -m eval
simulate:
	python -m eval.simulate_regressions
gate:
	python -m gates
experiment:
	@echo "make experiment is Tier 2 (live LLM); not enabled in Tier 1"
all: test eval simulate gate
