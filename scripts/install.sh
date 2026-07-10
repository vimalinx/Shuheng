#!/bin/sh
set -eu

REPO_URL="https://github.com/vimalinx/Shuheng"
DEFAULT_TAG="v0.2.0-alpha.1"

die() {
    printf 'shuheng installer: %s\n' "$*" >&2
    exit 1
}

log() {
    printf '%s\n' "$*"
}

usage() {
    cat <<'EOF'
Install Shuheng experimental local alpha.

Supported platforms:
  Linux                 supported alpha target
  Windows via WSL2      recommended Windows path
  macOS                 best-effort, unverified
  Windows native        unsupported; use WSL2

Usage:
  sh scripts/install.sh [options]
  curl -fsSL https://raw.githubusercontent.com/vimalinx/Shuheng/main/scripts/install.sh | sh

Options:
  --install-dir DIR, --prefix DIR
      Install virtual environment under DIR.
      Default: $HOME/.local/share/shuheng

  --bin-dir DIR
      Install launcher scripts into DIR.
      Default: $HOME/.local/bin

  --version TAG, --tag TAG
      Install from a GitHub release tag.
      Default: v0.2.0-alpha.1

  --wheel-url URL
      Install this exact wheel URL instead of deriving one from --version.

  --source PATH
      Install from a local source checkout or sdist path instead of a release wheel.

  --editable
      Use pip editable mode with --source PATH.

  --skip-agent-gateway-skill, --no-agent-gateway-skill
      Do not install the bundled shuheng-agent-gateway skill into ~/.agents/skills.

  --skip-check, --no-check
      Do not run shuheng-check after installation.

  --dry-run
      Print the actions that would run without creating files or installing packages.

  -h, --help
      Show this help.

Environment overrides:
  PYTHON                         Python executable to use.
  SHUHENG_INSTALL_DIR            Same as --install-dir.
  SHUHENG_BIN_DIR                Same as --bin-dir.
  SHUHENG_INSTALL_VERSION        Same as --version.
  SHUHENG_INSTALL_WHEEL_URL      Same as --wheel-url.
  SHUHENG_INSTALL_SOURCE         Same as --source.
  SHUHENG_INSTALL_DRY_RUN=1      Same as --dry-run.

Notes:
  The installer verifies or installs the pinned permanent OMP runtime with
  `shuheng runtime setup-omp`. If Bun is missing, it stops with the exact setup
  action instead of reporting a usable Shuheng installation.

  The optional Pi-native worker SDK can be installed later with
  `shuheng runtime setup-pi`.

  Shuheng is an experimental local alpha. It installs a local curses TUI and
  local JSONL stdio commands; native Windows users should run it through WSL2.
EOF
}

need_value() {
    [ "$#" -ge 2 ] || die "missing value for $1"
}

detect_platform() {
    uname_s=${SHUHENG_INSTALL_UNAME:-$(uname -s 2>/dev/null || printf unknown)}
    case "$uname_s" in
        Linux)
            osrelease_file=${SHUHENG_INSTALL_OSRELEASE_FILE:-/proc/sys/kernel/osrelease}
            if [ -r "$osrelease_file" ] && grep -qiE 'microsoft|wsl' "$osrelease_file"; then
                printf 'Windows via WSL2\n'
            else
                printf 'Linux\n'
            fi
            ;;
        Darwin)
            printf 'macOS\n'
            ;;
        MINGW* | MSYS* | CYGWIN*)
            die "native Windows is unsupported. Install Ubuntu on WSL2 and run this script inside WSL2."
            ;;
        *)
            die "unsupported platform '$uname_s'. Shuheng alpha supports Linux, WSL2, and best-effort macOS."
            ;;
    esac
}

find_python() {
    if [ -n "${PYTHON:-}" ]; then
        candidates=$PYTHON
    else
        candidates="python3 python"
    fi

    for candidate in $candidates; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
            command -v "$candidate"
            return 0
        fi
    done

    die "Python 3.10 or newer is required. Install python3, then rerun this installer."
}

tag_to_package_version() {
    tag_no_v=${1#v}
    case "$tag_no_v" in
        *-alpha.*)
            base=${tag_no_v%%-alpha.*}
            prerelease=${tag_no_v#*-alpha.}
            [ -n "$base" ] && [ -n "$prerelease" ] || return 1
            printf '%sa%s' "$base" "$prerelease"
            ;;
        *)
            printf '%s' "$tag_no_v"
            ;;
    esac
}

run_cmd() {
    if [ "$DRY_RUN" = "1" ]; then
        printf '+'
        for arg in "$@"; do
            printf ' %s' "$arg"
        done
        printf '\n'
        return 0
    fi
    "$@"
}

make_dir() {
    if [ "$DRY_RUN" = "1" ]; then
        printf '+ mkdir -p %s\n' "$1"
        return 0
    fi
    mkdir -p "$1"
}

install_launcher() {
    name=$1
    target="$BIN_DIR/$name"
    source_script="$VENV_DIR/bin/$name"
    if [ "$DRY_RUN" = "1" ]; then
        printf '+ write launcher %s -> %s\n' "$target" "$source_script"
        return 0
    fi
    tmp="$target.tmp.$$"
cat > "$tmp" <<EOF
#!/bin/sh
BUN_ROOT="\${BUN_INSTALL:-\${HOME:-$HOME_DIR}/.bun}"
PATH="\$BUN_ROOT/bin:\${PATH:-}"
export PATH
exec "$source_script" "\$@"
EOF
    chmod 755 "$tmp"
    mv "$tmp" "$target"
}

path_contains() {
    case ":${PATH:-}:" in
        *":$1:"*) return 0 ;;
        *) return 1 ;;
    esac
}

HOME_DIR=${HOME:-}
[ -n "$HOME_DIR" ] || die "HOME is not set"

INSTALL_DIR=${SHUHENG_INSTALL_DIR:-"$HOME_DIR/.local/share/shuheng"}
BIN_DIR=${SHUHENG_BIN_DIR:-"$HOME_DIR/.local/bin"}
TAG=${SHUHENG_INSTALL_VERSION:-$DEFAULT_TAG}
WHEEL_URL=${SHUHENG_INSTALL_WHEEL_URL:-}
SOURCE_PATH=${SHUHENG_INSTALL_SOURCE:-}
EDITABLE=0
INSTALL_GATEWAY_SKILL=1
RUN_CHECK=1
DRY_RUN=${SHUHENG_INSTALL_DRY_RUN:-0}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --install-dir | --prefix)
            need_value "$@"
            INSTALL_DIR=$2
            shift 2
            ;;
        --install-dir=* | --prefix=*)
            INSTALL_DIR=${1#*=}
            shift
            ;;
        --bin-dir)
            need_value "$@"
            BIN_DIR=$2
            shift 2
            ;;
        --bin-dir=*)
            BIN_DIR=${1#*=}
            shift
            ;;
        --version | --tag)
            need_value "$@"
            TAG=$2
            shift 2
            ;;
        --version=* | --tag=*)
            TAG=${1#*=}
            shift
            ;;
        --wheel-url)
            need_value "$@"
            WHEEL_URL=$2
            shift 2
            ;;
        --wheel-url=*)
            WHEEL_URL=${1#*=}
            shift
            ;;
        --source)
            need_value "$@"
            SOURCE_PATH=$2
            shift 2
            ;;
        --source=*)
            SOURCE_PATH=${1#*=}
            shift
            ;;
        --editable)
            EDITABLE=1
            shift
            ;;
        --skip-agent-gateway-skill | --no-agent-gateway-skill)
            INSTALL_GATEWAY_SKILL=0
            shift
            ;;
        --install-agent-gateway-skill)
            INSTALL_GATEWAY_SKILL=1
            shift
            ;;
        --skip-check | --no-check)
            RUN_CHECK=0
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

[ "$DRY_RUN" = "0" ] || DRY_RUN=1

if [ -n "$SOURCE_PATH" ] && [ -n "$WHEEL_URL" ]; then
    die "use either --source or --wheel-url, not both"
fi

if [ "$EDITABLE" = "1" ] && [ -z "$SOURCE_PATH" ]; then
    die "--editable requires --source PATH"
fi

PLATFORM=$(detect_platform)
PYTHON_BIN=$(find_python)
VENV_DIR="$INSTALL_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ -z "$SOURCE_PATH" ] && [ -z "$WHEEL_URL" ]; then
    PACKAGE_VERSION=$(tag_to_package_version "$TAG")
    [ -n "$PACKAGE_VERSION" ] || die "could not derive package version from tag '$TAG'"
    WHEEL_URL="$REPO_URL/releases/download/$TAG/shuheng-$PACKAGE_VERSION-py3-none-any.whl"
fi

log "Shuheng installer"
log "Platform: $PLATFORM"
log "Install dir: $INSTALL_DIR"
log "Bin dir: $BIN_DIR"
if [ -n "$SOURCE_PATH" ]; then
    log "Install target: source $SOURCE_PATH"
else
    log "Install target: $WHEEL_URL"
fi

make_dir "$INSTALL_DIR"
make_dir "$BIN_DIR"

run_cmd "$PYTHON_BIN" -m venv "$VENV_DIR"
run_cmd "$VENV_PYTHON" -m pip install --upgrade pip

if [ -n "$SOURCE_PATH" ]; then
    if [ "$EDITABLE" = "1" ]; then
        run_cmd "$VENV_PYTHON" -m pip install -e "$SOURCE_PATH"
    else
        run_cmd "$VENV_PYTHON" -m pip install "$SOURCE_PATH"
    fi
else
    run_cmd "$VENV_PYTHON" -m pip install "$WHEEL_URL"
fi

for script_name in shuheng shuheng-agent-bridge shuheng-agent-gateway shuheng-check shuheng-install-core-shim shuheng-integration; do
    install_launcher "$script_name"
done

log "Ensuring pinned OMP runtime is usable."
run_cmd "$BIN_DIR/shuheng" runtime setup-omp

if [ "$INSTALL_GATEWAY_SKILL" = "1" ]; then
    run_cmd "$BIN_DIR/shuheng" install-agent-gateway-skill
else
    log "Skipping shuheng-agent-gateway skill installation."
fi

if [ "$RUN_CHECK" = "1" ]; then
    run_cmd "$BIN_DIR/shuheng-check"
else
    log "Skipping shuheng-check."
fi

if ! path_contains "$BIN_DIR"; then
    log "PATH note: add $BIN_DIR to PATH before running shuheng from a new shell."
fi

log "Shuheng install complete."
