#!/usr/bin/env sh
set -eu

usage() {
    cat <<'EOF'
Usage: trust_lra_repos.sh [--root PATH] [--pattern GLOB] [--dry-run]

Trust local lra-* Git repositories for Git's safe.directory check.

Options:
  --root PATH     Parent directory to scan. Defaults to /mnt/f/repos when it
                  exists, then /f/repos when it exists, otherwise /repos.
  --pattern GLOB  Directory name pattern to match. Defaults to lra-*.
  --dry-run       Print the repositories that would be trusted.
  -h, --help      Show this help.
EOF
}

default_root() {
    if [ -d /mnt/f/repos ]; then
        printf '%s\n' /mnt/f/repos
    elif [ -d /f/repos ]; then
        printf '%s\n' /f/repos
    else
        printf '%s\n' /repos
    fi
}

root=$(default_root)
pattern='lra-*'
dry_run=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --root)
            if [ "$#" -lt 2 ]; then
                printf 'error: --root requires a value\n' >&2
                exit 2
            fi
            root=$2
            shift 2
            ;;
        --pattern)
            if [ "$#" -lt 2 ]; then
                printf 'error: --pattern requires a value\n' >&2
                exit 2
            fi
            pattern=$2
            shift 2
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'error: unknown argument: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if ! command -v git >/dev/null 2>&1; then
    printf 'error: git was not found on PATH.\n' >&2
    exit 1
fi

if [ ! -d "$root" ]; then
    printf 'error: root directory does not exist: %s\n' "$root" >&2
    exit 1
fi

added=0
already_trusted=0
skipped=0
matched=0
existing_safe_directories=$(git config --global --get-all safe.directory 2>/dev/null || true)

for repo in "$root"/$pattern; do
    [ -e "$repo" ] || continue
    matched=1

    if [ ! -d "$repo" ]; then
        continue
    fi

    repo=$(cd "$repo" && pwd -P)

    if [ ! -e "$repo/.git" ]; then
        printf 'Skipping non-Git directory: %s\n' "$repo"
        skipped=$((skipped + 1))
        continue
    fi

    safe_path=$repo

    if printf '%s\n' "$existing_safe_directories" | grep -Fx -- "$safe_path" >/dev/null; then
        printf 'Already trusted: %s\n' "$safe_path"
        already_trusted=$((already_trusted + 1))
        continue
    fi

    if [ "$dry_run" -eq 1 ]; then
        printf 'Would trust: %s\n' "$safe_path"
        continue
    fi

    git config --global --add safe.directory "$safe_path"
    printf 'Trusted: %s\n' "$safe_path"
    existing_safe_directories="${existing_safe_directories}
${safe_path}"
    added=$((added + 1))
done

if [ "$matched" -eq 0 ]; then
    printf "No directories matching '%s' found under %s.\n" "$pattern" "$root"
    exit 0
fi

printf '\nSummary:\n'
printf '  Added:           %s\n' "$added"
printf '  Already trusted: %s\n' "$already_trusted"
printf '  Skipped:         %s\n' "$skipped"

if [ "$dry_run" -eq 1 ]; then
    printf '\nDry run only. Re-run without --dry-run to update global Git config.\n'
fi
