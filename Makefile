.PHONY: help test pre-commit lint format release blast _blast add-help-to-readme init git-hooks clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

clean: ## Remove caches and compiled files
	@find . -path './.venv' -prune -o -type f -name "*.pyc" -delete
	@find . -path './.venv' -prune -o -type d -name "__pycache__" -exec rm -rf {} +
	@find . -path './.venv' -prune -o -type d -name ".ruff_cache" -exec rm -rf {} +

init: git-hooks ## Initialise project for dev work
	uv sync

git-hooks: ## Install git hooks
	git config core.hooksPath .githooks

test: ## Run pytest
	bash ./scripts/test.sh

pre-commit: ## Run pre-commit on all files
	bash ./scripts/pre_commit.sh

lint: ## Run ruff linting
	bash ./scripts/lint.sh

format: ## Run formatting
	bash ./scripts/format.sh

release: ## Create a release commit and tag (Usage: make release VERSION=X.Y.Z)
	bash ./scripts/release.sh $(VERSION)

add-help-to-readme: ## Update README.md with CLI help text
	NO_COLOR=1 PYTHON_COLORS=0 uv run python scripts/add_help_to_readme.py

# (Internal) Run linters
_blast: pre-commit format lint add-help-to-readme

blast: ## Run linters and pre-commit (safely stashing untracked files)
	@UNTRACKED=$$(git ls-files --others --exclude-standard); \
	if [ -n "$$UNTRACKED" ]; then \
		STASH_MSG="blast-stash-$$(date +%s)"; \
		echo "Stashing untracked files..."; \
		git stash push --include-untracked --quiet -m "$$STASH_MSG" -- $$UNTRACKED; \
		trap 'echo "Restoring untracked files..."; git stash pop --quiet' EXIT INT TERM; \
	fi; \
	$(MAKE) _blast

