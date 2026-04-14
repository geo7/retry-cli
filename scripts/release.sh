#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

# Check for version argument
if [ $# -ne 1 ]; then
    echo "Usage: bash ./scripts/release.sh <X.Y.Z>"
    echo "Example: bash ./scripts/release.sh 0.1.0"
    exit 1
fi

NEW_VERSION="$1"
# Basic validation: ensure it looks like a version number (X.Y.Z)
if [[ ! "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in X.Y.Z format (e.g., 0.1.0). Got: $NEW_VERSION"
    exit 1
fi

TAG="v${NEW_VERSION}"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
EXPECTED_BRANCH="${RELEASE_BRANCH:-main}"

# 1. Safety Checks
if [ "${CURRENT_BRANCH}" != "${EXPECTED_BRANCH}" ]; then
    echo "Refusing to release from branch ${CURRENT_BRANCH}."
    echo "Switch to ${EXPECTED_BRANCH}, or override with RELEASE_BRANCH=${CURRENT_BRANCH} if this is intentional."
    exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: Unstaged or uncommitted changes - check git status."
    exit 1
fi

echo "Checking remote status..."
git fetch origin "${CURRENT_BRANCH}" --quiet
LOCAL_REV=$(git rev-parse HEAD)
REMOTE_REV=$(git rev-parse "origin/${CURRENT_BRANCH}")

if [ "$LOCAL_REV" != "$REMOTE_REV" ]; then
    echo "Error: Your local branch '${CURRENT_BRANCH}' is not in sync with 'origin/${CURRENT_BRANCH}'."
    echo "Please push or pull changes before releasing."
    exit 1
fi

CURRENT_VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path

print(tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"])
PY
)"

if [ "${NEW_VERSION}" = "${CURRENT_VERSION}" ]; then
    echo "Error: pyproject.toml is already at version ${NEW_VERSION}."
    echo "Choose a new version before releasing."
    exit 1
fi

if git rev-parse "${TAG}" >/dev/null 2>&1; then
    echo "Error: Tag ${TAG} already exists locally."
    exit 1
fi

# 2. Bump Version
echo "Bumping version to ${NEW_VERSION} in pyproject.toml..."
# Update the version inside the [project] section, then parse the TOML back to
# confirm the file is still valid and the new value was written correctly.
python3 - <<PY
import re
import tomllib
from pathlib import Path

new_version = "${NEW_VERSION}"
path = Path("pyproject.toml")
content = path.read_text()

project_match = re.search(r"(?ms)^\\[project\\]\\n(?P<body>.*?)(?=^\\[|\\Z)", content)
if project_match is None:
    raise SystemExit("Error: Could not find [project] section in pyproject.toml.")

project_body = project_match.group("body")
updated_body, replacements = re.subn(
    r'^version\\s*=\\s*"[^"]+"',
    f'version = "{new_version}"',
    project_body,
    count=1,
    flags=re.MULTILINE,
)

if replacements != 1:
    raise SystemExit("Error: Could not update project.version in pyproject.toml.")

new_content = (
    content[:project_match.start("body")]
    + updated_body
    + content[project_match.end("body"):]
)
path.write_text(new_content)

parsed_version = tomllib.loads(path.read_text())["project"]["version"]
if parsed_version != new_version:
    raise SystemExit(
        f"Error: Expected project.version to be {new_version}, but found {parsed_version}."
    )
PY

echo "Running verification steps for ${TAG}..."
CI=true bash ./scripts/lint.sh
CI=true bash ./scripts/test.sh

# Just check that package builds.
uv build

echo "Committing version bump..."
git add pyproject.toml
git commit -m "chore: bump version to ${TAG}"

echo "Creating annotated tag ${TAG}..."
git tag -a "${TAG}" -m "Release ${TAG}"

echo "--------------------------------------------------"
echo "Release ${TAG} prepared successfully!"
echo "Review the changes and then push both the commit and the tag:"
echo ""
echo "git push origin ${CURRENT_BRANCH} ${TAG}"
echo "--------------------------------------------------"
