import pytest

from retry_cli import __main__ as retry_main


def test_parse_command_rejects_empty_input():
    """Empty command strings should be rejected before execution starts.

    GIVEN: `parse_command()` receives an empty command string
    WHEN: the command string is validated
    THEN: a `UsageError` should be raised with an empty-command message
    """
    with pytest.raises(retry_main.UsageError, match="command cannot be empty"):
        retry_main.parse_command("")


def test_parse_command_rejects_invalid_shell_quoting():
    """Malformed shell quoting should be reported as a usage error.

    GIVEN: `parse_command()` receives an invalid shell-quoted string
    WHEN: the command string is parsed
    THEN: a `UsageError` should be raised with an invalid-command message
    """
    with pytest.raises(retry_main.UsageError, match="invalid command string"):
        retry_main.parse_command("'unterminated")
