.PHONY: format lint typecheck test architecture quality doctor plan smoke

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

lint:
	uv run ruff format --check src tests
	uv run ruff check src tests

typecheck:
	uv run pyright

test:
	uv run pytest

architecture:
	uv run pytest tests/architecture tests/unit/config tests/integration/cli tests/e2e tests/smoke

quality: lint typecheck architecture
	uv run lint-imports
	uv run deptry src
	uv run vulture src

doctor:
	uv run fedcampaign doctor

plan:
	uv run fedcampaign plan

smoke:
	uv run fedcampaign smoke
