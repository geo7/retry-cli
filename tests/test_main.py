from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from retry_cli import __main__ as retry_main

if TYPE_CHECKING:
    from pathlib import Path


def write_script(path: Path, content: str) -> Path:
    path.write_text(dedent(content))
    path.chmod(0o755)
    return path


def test_main_happy_path_silences_first_attempt(capfd):
    """A successful first run should exit cleanly and stay silent by default.

    GIVEN: `main()` is called with a command that succeeds immediately
    WHEN: the command is executed without `show_first=True`
    THEN: the process should exit with code 0 and not surface the first run output
    """
    with pytest.raises(SystemExit) as exc_info:
        retry_main.main(command="echo 'hello'")

    captured = capfd.readouterr()
    assert exc_info.value.code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_main_show_first_makes_initial_run_visible(capfd):
    """The first attempt should be visible when `show_first` is enabled.

    GIVEN: `main()` is called with a command that succeeds immediately
    WHEN: the command is executed with `show_first=True`
    THEN: the first run output should be written to stdout
    """
    with pytest.raises(SystemExit) as exc_info:
        retry_main.main(command="echo 'hello'", show_first=True)

    captured = capfd.readouterr()
    assert exc_info.value.code == 0
    assert "hello" in captured.out


def test_main_zero_retries_runs_once(capfd):
    """Zero retries should still run the command exactly once.

    GIVEN: `main()` is called with `retries=0`
    WHEN: the command succeeds on its only attempt
    THEN: the process should exit with code 0 and show the output from that single run
    """
    with pytest.raises(SystemExit) as exc_info:
        retry_main.main(command="echo 'once'", retries=0)

    captured = capfd.readouterr()
    assert exc_info.value.code == 0
    assert "once" in captured.out


def test_main_retries_until_success(tmp_path, capfd, caplog):
    """A failing command should retry until it succeeds.

    GIVEN: `main()` is called with a script that fails once and then succeeds
    WHEN: the retry loop runs with retries enabled
    THEN: the command should retry, log the retry, and exit with code 0
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

    with caplog.at_level(logging.INFO, logger="retry"), pytest.raises(SystemExit) as exc_info:
        retry_main.main(command=f"bash {flaky_script}", retries=2)

    captured = capfd.readouterr()
    assert exc_info.value.code == 0
    assert "[retry] Command failed. Attempt 2 of 3" in caplog.text
    assert "Marker found! Success." in captured.out


def test_main_returns_last_failure_code(tmp_path, caplog):
    """The final failing return code should be returned to the caller.

    GIVEN: `main()` is called with a script that always exits non-zero
    WHEN: all configured retries are exhausted
    THEN: the process should exit with the last failure code and log each retry
    """
    failing_script = write_script(
        tmp_path / "always_fail.sh",
        """#!/bin/bash
        echo "Nope."
        exit 9
        """,
    )

    with caplog.at_level(logging.INFO, logger="retry"), pytest.raises(SystemExit) as exc_info:
        retry_main.main(command=f"bash {failing_script}", retries=2)

    assert exc_info.value.code == 9
    assert "[retry] Command failed. Attempt 2 of 3" in caplog.text
    assert "[retry] Command failed. Attempt 3 of 3" in caplog.text


def test_main_success_code_is_respected(tmp_path, capfd):
    """A configured success code should override the default zero-only success rule.

    GIVEN: `main()` is called with `success_code=1`
    WHEN: the underlying command exits with code 1
    THEN: the process should treat that result as success and exit with code 0
    """
    script = write_script(
        tmp_path / "exit_one.sh",
        """#!/bin/bash
        exit 1
        """,
    )

    with pytest.raises(SystemExit) as exc_info:
        retry_main.main(command=f"bash {script}", success_code=1)

    captured = capfd.readouterr()
    assert exc_info.value.code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_main_command_not_found_exits_127(capfd):
    """A missing command should produce the standard shell error exit code.

    GIVEN: `main()` is called with a command that cannot be found
    WHEN: subprocess execution cannot locate the executable
    THEN: the process should exit with code 127 and print a plain error message
    """
    with pytest.raises(SystemExit) as exc_info:
        retry_main.main(command="nonexistent-command")

    captured = capfd.readouterr()
    assert exc_info.value.code == 127
    assert "Error: Command not found: nonexistent-command" in captured.err


def test_main_keyboard_interrupt_exits_130(caplog):
    """A keyboard interrupt should map to the standard interrupted-process exit code.

    GIVEN: `main()` is running a long-lived command
    WHEN: the parent process receives SIGINT during execution
    THEN: the process should exit with code 130 and report that the user aborted it
    """
    timer = threading.Timer(0.1, lambda: os.kill(os.getpid(), signal.SIGINT))

    try:
        timer.start()
        with pytest.raises(SystemExit) as exc_info:
            retry_main.main(command=f'{sys.executable} -c "import time; time.sleep(10)"')
    finally:
        timer.cancel()

    assert exc_info.value.code == 130
    assert "Aborted by user." in caplog.text


def test_entry_point_runs_valid_cli_args(monkeypatch, capfd):
    """The CLI entry point should run valid CLI arguments successfully.

    GIVEN: `entry_point()` is called with valid CLI arguments in `sys.argv`
    WHEN: argparse parses those arguments and `main()` executes them
    THEN: the command should run successfully and surface the expected output
    """
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "retry",
            "--retries",
            "0",
            "--show-first",
            "--command",
            "echo hi",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        retry_main.entry_point()

    captured = capfd.readouterr()
    assert exc_info.value.code == 0
    assert "hi" in captured.out


def test_entry_point_rejects_negative_retries(monkeypatch, capsys):
    """Negative retry counts should be rejected by argparse.

    GIVEN: `entry_point()` is called with `--retries -1`
    WHEN: argparse validates the CLI arguments
    THEN: it should exit with code 2 and print the retry validation error
    """
    monkeypatch.setattr(
        sys,
        "argv",
        ["retry", "--retries", "-1", "--command", "false"],
    )

    with pytest.raises(SystemExit) as exc_info:
        retry_main.entry_point()

    assert exc_info.value.code == 2
    assert "argument --retries: must be at least 0" in capsys.readouterr().err


def test_entry_point_converts_usage_errors_into_parser_errors(monkeypatch, capsys):
    """Usage errors raised by the implementation should be surfaced as parser errors.

    GIVEN: `entry_point()` is called with an invalid command value
    WHEN: `main()` raises a `UsageError` during execution
    THEN: the parser should exit with code 2 and print the usage error message
    """
    monkeypatch.setattr(
        sys,
        "argv",
        ["retry", "--command", ""],
    )

    with pytest.raises(SystemExit) as exc_info:
        retry_main.entry_point()

    assert exc_info.value.code == 2
    assert "command cannot be empty" in capsys.readouterr().err
