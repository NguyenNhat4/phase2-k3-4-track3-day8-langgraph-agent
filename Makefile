.PHONY: install test lint typecheck run-scenarios grade-local clean

# Use uv's managed environment for every target. The OpenAI extra matches the
# provider configured by the lab's .env; change it to google or anthropic when
# using another provider.
UV_CACHE_DIR ?= .uv-cache
UV_RUN := UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --extra dev --extra openai

install:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --extra dev --extra openai

test:
	$(UV_RUN) pytest

lint:
	$(UV_RUN) ruff check src tests

typecheck:
	$(UV_RUN) mypy src

run-scenarios:
	$(UV_RUN) python -m langgraph_agent_lab.cli run-scenarios --config configs/lab.yaml --output outputs/metrics.json

grade-local:
	$(UV_RUN) python -m langgraph_agent_lab.cli validate-metrics --metrics outputs/metrics.json

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .uv-cache htmlcov dist build *.egg-info outputs/*.json
