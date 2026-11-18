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
# `slow` is a local ergonomics marker: `make test` (and CI/release) still runs
# those modules; only the optional `make test-fast` excludes them.
FAST := -m "not integration and not container_target"
TEST_FAST := -m "not integration and not container_target and not slow"

.PHONY: help sync collections install test test-fast test-shard test-integration lint format dev dev-hermetic gates-diff gates-role gates gates-ci gates-pin pin-audit release-preflight hermetic hermetic-shard lock-check docs-check build assets-parity ci-gates-parity clean

help:
	@echo "sync             Install the env from uv.lock (uv sync --frozen)"
	@echo "collections      Install the pinned Ansible collections into .collections/"
	@echo "test             Run the fast suite (excludes integration/container_target)"
	@echo "test-fast        Fast suite minus modules marked slow (optional local run)"
	@echo "test-shard       Run one deterministic shard (SHARD=I/N, e.g. SHARD=1/4)"
	@echo "test-integration Run the real-ansible and disposable-container suites"
	@echo "release-preflight Read-only release checks (TAG=vX.Y.Z optional; no tag is created)"
	@echo "dev              Changed-file feedback gate (NOT release proof; make gates is authoritative)"
	@echo "dev-hermetic     dev with empty HOME/XDG and a foreign cwd (HERMETIC=1)"
	@echo "gates-diff       dev against BASE (default origin/main, then main)"
	@echo "gates-role       Mapped checks/tests for one Ansible role (ROLE=<role>)"
	@echo "lint             Ruff check src/ and tests/"
	@echo "format           Ruff format src/ and tests/"
	@echo "hermetic         Run the fast suite with empty HOME/XDG and a foreign cwd"
	@echo "hermetic-shard   Run one hermetic shard (SHARD=I/N, e.g. SHARD=1/4)"
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

# REQ-055: optional local shortcut. Slow-marked modules still run in `make test`,
# CI, hermetic, and release; only this target skips them.
test-fast: collections
	$(UV) run pytest -q $(TEST_FAST)

# REQ-055: one deterministic file shard. `make test` stays the full fast suite;
# CI runs all I/N selections so every file still executes exactly once.
test-shard: collections
	@test -n "$(SHARD)" || { echo "usage: make test-shard SHARD=I/N"; exit 2; }
	@files=$$($(UV) run python scripts/pytest_shard.py --shard "$(SHARD)" --fast --list); rc=$$?; \
	test $$rc -eq 0 || exit $$rc; \
	test -n "$$files" || { echo "no test files selected for shard $(SHARD)"; exit 1; }; \
	$(UV) run pytest -q $(FAST) $$files

test-integration: collections
	$(UV) run pytest -q -m "integration or container_target"

# REQ-055: read-only pre-tag check. It never creates or pushes a tag and never
# applies anything. Keep it OUT of GATES: it is a release ritual, not a gate.
release-preflight:
	$(UV) run python scripts/release_preflight.py $(if $(TAG),--tag "$(TAG)",) $(if $(BRANCH),--branch "$(BRANCH)",)

# REQ-054: changed-file feedback only. `make gates`/CI remain the release
# authority. The mapping is explicit in scripts/gate-map.yaml and fails closed
# (unknown/gate-sensitive/zero-test paths run the full fast suite). Diffs use
# the merge-base with BASE plus working-tree, staged, and untracked changes.
# HERMETIC=1 (or `make dev-hermetic`) scrubs HOME/XDG and uses a foreign cwd.
# DRY_RUN=1 prints the resolved base and mapping without running anything.
dev:
	$(UV) run python scripts/gate_diff.py $(if $(BASE),--base "$(BASE)",) $(if $(HERMETIC),--hermetic,) $(if $(DRY_RUN),--dry-run,)

dev-hermetic:
	$(MAKE) dev HERMETIC=1 BASE="$(BASE)" DRY_RUN="$(DRY_RUN)"

gates-diff:
	$(UV) run python scripts/gate_diff.py $(if $(BASE),--base "$(BASE)",) $(if $(HERMETIC),--hermetic,) $(if $(DRY_RUN),--dry-run,)

gates-role:
	@test -n "$(ROLE)" || { echo "usage: make gates-role ROLE=<role>"; exit 2; }
	$(UV) run python scripts/gate_diff.py --role "$(ROLE)" $(if $(HERMETIC),--hermetic,) $(if $(DRY_RUN),--dry-run,)

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

# REQ-056: the same hermetic environment, restricted to one deterministic file
# shard. The file list is made absolute because pytest runs from a foreign cwd.
hermetic-shard: collections
	@test -n "$(SHARD)" || { echo "usage: make hermetic-shard SHARD=I/N"; exit 2; }
	@test -x "$(PYTHON)" || { echo "run 'make sync' first"; exit 1; }
	@files=$$($(UV) run python scripts/pytest_shard.py --shard "$(SHARD)" --fast --list | sed "s#^#$(CURDIR)/#"); rc=$$?; \
	test $$rc -eq 0 || exit $$rc; \
	test -n "$$files" || { echo "no test files selected for hermetic shard $(SHARD)"; exit 1; }; \
	tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	mkdir -p "$$tmp/cwd"; \
	cd "$$tmp/cwd" && \
	env HOME="$$tmp/home" \
	    XDG_CONFIG_HOME="$$tmp/config" XDG_CACHE_HOME="$$tmp/cache" \
	    XDG_DATA_HOME="$$tmp/data" XDG_STATE_HOME="$$tmp/state" \
	    TMPDIR="$$tmp" \
	    PATH="$(CURDIR)/.venv/bin:$$PATH" \
	    ANSIBLE_COLLECTIONS_PATH="$(CURDIR)/.collections" \
	    PYTHONPATH="$(CURDIR)/src:$(CURDIR)" \
	    "$(PYTHON)" -m pytest -q $(FAST) $$files \
	        -c "$(CURDIR)/pyproject.toml" --rootdir="$(CURDIR)"

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

# Pin-only preflight: all engine asset/contract/platform mirrors match the
# composition fixture, and the skin plane names exactly the released five
# manifests, ten CSS targets and the rofi rasi artifact. Use `gates-pin` for
# version/fixture-only changes; keep `gates` (full test + hermetic) for
# behavior/schema changes.
pin-audit:
	python3 scripts/pin-audit.py

gates-pin: pin-audit lint docs-check ci-gates-parity

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
	python3 scripts/check-wheel-contents.py

clean:
	rm -rf dist .pytest_cache .ruff_cache .coverage htmlcov
