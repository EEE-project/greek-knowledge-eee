# greek-knowledge-eee -- contributor tooling: lint, validate the committed knowledge base, run the tests.
# `make` alone lists the targets; `make all` is what to run before a commit or a PR.

# uv only warns about an ambient VIRTUAL_ENV (this org keeps a shared ~/.venv/eee) and older uv used it,
# so unset it: every target then runs in this repo's own .venv.
UV ?= env -u VIRTUAL_ENV uv
# ruff is not a locked dev dependency here. Stay on 0.15: 0.16 switches on many more default rules,
# which flag existing code. Override with e.g. `make lint RUFF=ruff`.
RUFF ?= $(UV) run --with 'ruff>=0.15,<0.16' ruff

.PHONY: help all check lint validate test

help:
	@echo "make lint       ruff check ."
	@echo "make validate   greek-knowledge check: well-formed concept files, canonical footnotes, current verification records"
	@echo "make check      lint + validate"
	@echo "make test       pytest -m 'not integration' (no network; never touches tracked content)"
	@echo "make all        check + test"

all: check test

check: lint validate

lint:
	$(RUFF) check .

validate:
	$(UV) run greek-knowledge check

test:
	$(UV) run pytest -m "not integration" -q
