#!/usr/bin/env bash
# PreToolUse hook: run lint and tests on the staged snapshot before Claude runs `git commit`.
# Exit 2 blocks the commit and shows stderr to Claude; any other Bash call passes through.
set -o pipefail

if ! command -v jq >/dev/null; then
    echo "Pre-commit check failed: jq is not installed, so the hook can't read the command" >&2
    exit 2
fi
if ! command=$(jq -r '.tool_input.command // ""'); then
    echo "Pre-commit check failed: couldn't parse the hook input" >&2
    exit 2
fi

# Matches `git commit`, `git  commit`, `git -C path commit`, `git -c key=value commit`, after a command separator.
commit_re='(^|[;&|[:space:]])git([[:space:]]+-[cC][[:space:]]+[^[:space:]]+)*[[:space:]]+commit([[:space:]]|$)'
[[ "$command" =~ $commit_re ]] || exit 0

root=${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)} || exit 2

# Check what will be committed (the index), not the working tree.
snapshot=$(mktemp -d) || exit 2
trap 'rm -rf "$snapshot"' EXIT
git -C "$root" checkout-index --all --prefix="$snapshot/" || exit 2
cd "$snapshot" || exit 2

run_check() {
    local output
    if ! output=$(uv run --project "$root" --locked "$@" 2>&1); then
        echo "Pre-commit check failed on the staged changes: $*" >&2
        echo "$output" >&2
        exit 2
    fi
}

run_check ruff check .
run_check ruff format --check .
run_check pytest -q -p no:cacheprovider
