from __future__ import annotations

import subprocess
from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def write_script(path: Path, content: str) -> Path:
    path.write_text(dedent(content))
    path.chmod(0o755)
    return path


def test_cli_show_first_integration():
    """The installed console entry point should still work end to end.

    GIVEN: the real `retry` CLI is invoked through `uv run`
    WHEN: it is run with `--show-first` and a simple echo command
    THEN: it should exit successfully and print the command output
    """
    result = subprocess.run(
        ["uv", "run", "retry", "--show-first", "--command", "echo 'hello'"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "hello" in result.stdout


def test_cli_retries_real_script(tmp_path):
    """The real CLI should retry a flaky script until it succeeds.

    GIVEN: a shell script that fails once and then succeeds on the next run
    WHEN: the real `retry` CLI executes it with retries enabled
    THEN: it should log the retry, succeed overall, and surface the successful output
    """
    marker_file = tmp_path / "marker.txt"
    flaky_script = write_script(
        tmp_path / "flaky.sh",
        f"""#!/bin/bash
        if [ -f "{marker_file}" ]; then
            echo "Marker found! Success."
            exit 0
        else
            echo "Marker missing! Creating it and failing."
            touch "{marker_file}"
            exit 1
        fi
        """,
    )

    result = subprocess.run(
        ["uv", "run", "retry", "--retries", "2", "--command", f"bash {flaky_script}"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "[retry] Command failed. Attempt 2 of 3" in result.stderr
    assert "Marker found! Success." in result.stdout
