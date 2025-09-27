PYTHON ?= python
PACKAGE = src/quantbobe
CONFIG = $(PACKAGE)/config/default.yaml

.PHONY: setup lint typecheck test backtest report live clean

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

lint:
	ruff check src tests

format:
	black src tests
	ruff check --fix src tests

format-check:
	black --check src tests
	ruff check src tests

typecheck:
	mypy src

test:
	pytest

backtest:
	$(PYTHON) -m src.quantbobe.cli backtest --config $(CONFIG)

report:
	$(PYTHON) -m src.quantbobe.cli report --config $(CONFIG)

live:
	$(PYTHON) -m src.quantbobe.live.run_live --config $(CONFIG)

clean:
	rm -rf __pycache__ */__pycache__ .mypy_cache .pytest_cache
