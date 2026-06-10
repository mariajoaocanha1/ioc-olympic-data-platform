.PHONY: run test lint typecheck all

run:
	python -m src.olympics_pipeline.main

test:
	pytest tests/ -v --cov=src

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

all: lint typecheck test run
