"""Add CLI help output to the README usage section."""

from io import StringIO
from pathlib import Path

from retry_cli.__main__ import get_parser

README_PATH = Path("README.md")
EXPECTED_SPLITS = 3


def cli_help_text() -> str:
    """Get --help from argparse parser."""
    parser = get_parser()
    cli_help = StringIO()
    parser.print_help(file=cli_help)
    return cli_help.getvalue()


def update_readme_cli_help() -> str:
    """Generate README with updated cli --help."""
    result = cli_help_text()
    readme = README_PATH.read_text()
    split_string = "[comment]: # (CLI help split)\n"
    splits = readme.split(split_string)
    if len(splits) != EXPECTED_SPLITS:
        # Fallback if the split comments aren't found or are incorrect
        return readme
    return splits[0] + split_string + "\n```text\n" + result + "```\n\n" + split_string + splits[2]


def main() -> int:
    """Update README.md with the current CLI help text."""
    updated_readme = update_readme_cli_help()
    README_PATH.write_text(updated_readme)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
