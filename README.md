# retry-cli

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI Latest Release](https://img.shields.io/pypi/v/retry-cli.svg)](https://pypi.org/project/retry-cli/)
[![License](https://img.shields.io/pypi/l/retry-cli.svg)](https://github.com/geo7/retry-cli/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/retry-cli.svg)](https://pypi.org/project/retry-cli/)
[![CI Status](https://github.com/geo7/retry-cli/actions/workflows/test.yml/badge.svg)](https://github.com/geo7/retry-cli/actions)

A utility to run a shell command a set number of times with automatic retries on failure.

Mainly created as having tools such as `pre-commit`, `format`, etc fail once then pass the second time is (to me!) quite annoying. Often they'll fail once, then pass the second time.

Example usage:

```sh
uvx --from retry-cli retry --command "pre-commit run --all-files"
```

## Usage

[comment]: # (CLI help split)

```text
usage: retry [-h] --command COMMAND [--retries RETRIES] [--show-first]
             [--success-code SUCCESS_CODE]

Run shell command with automatic retries on failure.

Usage Examples:
  retry --retries 4 --show-first --command "pre-commit run --all-files"

Useful for auto-formatters and tools like pre-commit, which might fail one or
more times but ultimately pass.

options:
  -h, --help            show this help message and exit
  --command COMMAND     The command string to execute.
  --retries RETRIES     Number of retries after the first attempt (default: 2).
  --show-first          Show output of the first attempt (default: hidden).
  --success-code SUCCESS_CODE
                        The exit code that indicates success (default: 0).
```

[comment]: # (CLI help split)

## Installation

Given this is a simple CLI tool it's recommended to use `pipx / uvx` to run with.

### `uvx`

```bash
# PyPI
uvx --from retry-cli retry --command "pre-commit run --all-files"
# GitHub
uvx --from git+https://github.com/geo7/retry-cli.git retry --command "..."
```

## Development

```bash
make init   # setup project
make test   # run tests
make blast  # run linting
```

## Release

Manual release process, merge feature into `main` then:

Run release script:

    make release VERSION=0.1.0

Push commit:

    git push origin main v0.1.0

Which will trigger [GitHub Release workflow](.github/workflows/release.yml).

# Alternatives

Some how when googling before creating this I missed the following: https://github.com/dbohdan/recur , it looks good! I can't think of a reason someone would use this rather than recur, so unless you particularly want to use a tool written in python recur seems worth a look.
