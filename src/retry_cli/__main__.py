"""Util to run a shell command a set number of times.

Useful for tools such as pre-commit / auto-formatters. Often they'll fail on
the first try and pass on the second, and I cba to re-run them.

Default is to have the first attempt silent, and the final attempt return
whatever the output was.

So an auto-formatter might have something like (assuming 2 retries):

Resolves:

    fail (silent)
    fail (silent)
    pass (output result)

Fails:

    fail (silent)
    fail (silent)
    fail (output result)


If the tool passes earlier, eg on the second run, it'll exit on the second run
with the report output.
"""

import argparse
import logging
import shlex
import subprocess
import sys

# Configure logging to output to stderr with a simple format
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
logger = logging.getLogger("retry")

# Standard exit codes
EXIT_COMMAND_NOT_FOUND = 127
EXIT_INTERRUPTED = 130


class UsageError(ValueError):
    """Raised when the user provides invalid CLI input."""


def non_negative_int(value: str) -> int:
    """Parse a CLI integer that must be at least 0."""
    parsed = int(value)
    if parsed < 0:
        msg = "must be at least 0"
        raise argparse.ArgumentTypeError(msg)
    return parsed


def parse_command(command: str) -> list[str]:
    """Validate and split the requested command string."""
    if not command.strip():
        msg = "command cannot be empty"
        raise UsageError(msg)

    try:
        cmd_list = shlex.split(command)
    except ValueError as exc:
        msg = f"invalid command string: {exc}"
        raise UsageError(msg) from exc

    return cmd_list


def get_parser() -> argparse.ArgumentParser:
    """Create the argument parser for retry-cli."""
    description = """
Run shell command with automatic retries on failure.

Usage Examples:
  retry --retries 4 --show-first --command "pre-commit run --all-files"

Useful for auto-formatters and tools like pre-commit, which might fail one or
more times but ultimately pass.
"""
    parser = argparse.ArgumentParser(
        prog="retry",
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--command", required=True, help="The command string to execute.")
    parser.add_argument(
        "--retries",
        type=non_negative_int,
        default=2,
        help="Number of retries after the first attempt (default: 2).",
    )
    parser.add_argument(
        "--show-first",
        action="store_true",
        help="Show output of the first attempt (default: hidden).",
    )
    parser.add_argument(
        "--success-code",
        type=int,
        default=0,
        help="The exit code that indicates success (default: 0).",
    )
    return parser


def main(
    *,
    command: str,
    retries: int = 2,
    show_first: bool = False,
    success_code: int = 0,
) -> None:
    """Execute the requested command with retries."""
    # Split command string into list for subprocess (handles quotes correctly)
    cmd_list = parse_command(command)
    attempts = retries + 1

    def run_command(*, silent: bool) -> subprocess.CompletedProcess:
        try:
            if silent:
                # The CLI intentionally executes a user-provided command string.
                return subprocess.run(cmd_list, check=False, capture_output=True)  # noqa: S603
            # The CLI intentionally executes a user-provided command string.
            return subprocess.run(cmd_list, check=False)  # noqa: S603
        except FileNotFoundError:
            sys.stderr.write(f"Error: Command not found: {cmd_list[0]}\n")
            sys.exit(EXIT_COMMAND_NOT_FOUND)
        except KeyboardInterrupt:
            logger.warning("\nAborted by user.")
            sys.exit(EXIT_INTERRUPTED)

    # First Attempt: silent by default unless show_first is True or it's the
    # only attempt.
    is_single_run = attempts == 1
    first_run_silent = (not show_first) and (not is_single_run)

    result = run_command(silent=first_run_silent)

    if result.returncode == success_code:
        sys.exit(0)

    # Retry Loop: we already used 1 attempt.
    for attempt in range(2, attempts + 1):
        logger.info("\n[retry] Command failed. Attempt %d of %d...", attempt, attempts)
        # Subsequent attempts are always visible
        result = run_command(silent=False)
        if result.returncode == success_code:
            sys.exit(0)

    # If we exit the loop, the last attempt failed.
    sys.exit(result.returncode)


def entry_point() -> None:
    """Entry point for the CLI command."""
    parser = get_parser()
    try:
        args = parser.parse_args()
        main(
            command=args.command,
            retries=args.retries,
            show_first=args.show_first,
            success_code=args.success_code,
        )
    except UsageError as exc:
        parser.error(str(exc))


if __name__ == "__main__":  # pragma: no cover
    entry_point()
