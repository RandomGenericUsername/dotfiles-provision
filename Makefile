# dotfiles-provision — fresh-clone rebuild with make.
#
# Fresh machine path:
#   1. `make sync`     (uv-managed env from the committed lock)
#   2. `make test`     (fast suite; real-ansible cases are opt-in)
#   3. `make gates`    (test + lint + hermetic + lock-check + docs-check)
#   4. `make build`    (sdist + wheel in dist/)
#   5. `make install`  (install the built package into the local .venv)
#
# Every target is anchored on $(CURDIR); none assumes a parent checkout.

UV     ?= uv
PYTHON := $(CURDIR)/.venv/bin/python

# Collections this engine's playbooks use (ansible.posix.synchronize,
# community.general, kewlfft.aur). Installed INSIDE the repo so `make hermetic`
# (empty HOME) and CI resolve the same pinned set instead of a developer's
# ~/.ansible. The directory is gitignored; `make sync` does not touch it.
export ANSIBLE_COLLECTIONS_PATH := $(CURDIR)/.collections

# The authoritative gate set. `make gates` runs it for a developer; CI runs one
# job per member (`.github/workflows/gates.yml`) and `make ci-gates-parity`
# fails when the two sets differ. Add a gate here AND a job there in one commit.
GATES := test lint hermetic lock-check docs-check

# The fast suite: unit + architecture + seam guards. The integration marker is
# for real `ansible-playbook` runs against the host; `container_target` needs a
# disposable root container. Both are developer proofs, not stock-runner gates.
FAST := -m "not integration and not container_target"

.PHONY: help sync collections install test test-integration lint format gates gates-ci hermetic lock-check docs-check build assets-parity ci-gates-parity clean

help:
	@echo "sync             Install the env from uv.lock (uv sync --frozen)"
	@echo "collections      Install the pinned Ansible collections into .collections/"
	@echo "test             Run the fast suite (excludes integration/container_target)"
	@echo "test-integration Run the real-ansible and disposable-container suites"
	@echo "lint             Ruff check src/ and tests/"
	@echo "format           Ruff format src/ and tests/"
	@echo "hermetic         Run the fast suite with empty HOME/XDG and a foreign cwd"
	@echo "lock-check       uv lock --check (the committed lock is current)"
	@echo "docs-check       README/CHANGELOG/LICENSE/AGENTS + CLAUDE symlink exist"
	@echo "gates            $(GATES)"
	@echo "ci-gates-parity  Workflow jobs equal GATES + declared CI-only jobs"
	@echo "assets-parity    Run AD-8.4 parity against the pinned dotfiles-assets corpus"
	@echo "build            Build sdist + wheel into dist/"
	@echo "install          Install the built package into .venv"
	@echo "clean            Remove dist/ and local caches"

sync:
	$(UV) sync --frozen

# Pinned collections for the playbooks. `-p .collections` keeps them inside the
# checkout (gitignored) so a scrubbed HOME still resolves the same set.
collections:
	$(UV) run ansible-galaxy collection install -r ansible/requirements.yml -p .collections

install: sync
	$(UV) pip install --reinstall .

test: collections
	$(UV) run pytest -q $(FAST)

test-integration: collections
	$(UV) run pytest -q -m "integration or container_target"

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests

# AD-8: pass with HOME and all four XDG roots pointing at empty temp dirs and an
# unrelated working directory. The composition is resolved through the fixture
# (tests/support.py), never through the caller's checkout, so the cwd cannot
# change the result.
hermetic: collections
	@test -x "$(PYTHON)" || { echo "run 'make sync' first"; exit 1; }
	@tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	mkdir -p "$$tmp/cwd"; \
	cd "$$tmp/cwd" && \
	env HOME="$$tmp/home" \
	    XDG_CONFIG_HOME="$$tmp/config" XDG_CACHE_HOME="$$tmp/cache" \
	    XDG_DATA_HOME="$$tmp/data" XDG_STATE_HOME="$$tmp/state" \
	    TMPDIR="$$tmp" \
	    PATH="$(CURDIR)/.venv/bin:$$PATH" \
	    ANSIBLE_COLLECTIONS_PATH="$(CURDIR)/.collections" \
	    PYTHONPATH="$(CURDIR)/src:$(CURDIR)" \
	    "$(PYTHON)" -m pytest -q $(FAST) \
	        -c "$(CURDIR)/pyproject.toml" --rootdir="$(CURDIR)" "$(CURDIR)/tests"

lock-check:
	$(UV) lock --check

docs-check:
	@test -f README.md      || { echo "missing README.md"; exit 1; }
	@test -f CHANGELOG.md   || { echo "missing CHANGELOG.md"; exit 1; }
	@test -f LICENSE        || { echo "missing LICENSE"; exit 1; }
	@test -f AGENTS.md      || { echo "missing AGENTS.md"; exit 1; }
	@test -L CLAUDE.md      || { echo "CLAUDE.md must be a symlink to AGENTS.md"; exit 1; }
	@grep -q "MIT License" LICENSE || { echo "LICENSE is not the MIT text"; exit 1; }

gates: $(GATES)

# Alias kept so a CI parity check and a local run name the same set.
gates-ci: $(GATES)

ci-gates-parity:
	python3 scripts/ci-gates-parity.py

# R-01: CI-only because it needs a network clone of the pinned assets repo.
# The runner clones the tag, exports the corpus env, and fails on a skipped
# parity test (a skip would be a silent pass). Run `make sync` first.
assets-parity:
	$(UV) run python scripts/assets-parity.py

build:
	$(UV) build

clean:
	rm -rf dist .pytest_cache .ruff_cache .coverage htmlcov
