#!/usr/bin/env bash
# PRAXIS Universal Kit — Unix Installer (macOS / Linux)
# =====================================================
# Usage: bash install.sh [--lang es] [--dir /path/to/project]
# Requirements: Python 3.8+, bash 3+
# No root/sudo required. No pip install.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRAXIS_VERSION="0.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PROJECT_DIR="$(pwd)"
LANG="en"
PROJECT_DIR="$DEFAULT_PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang)   LANG="$2"; shift 2 ;;
        --dir)    PROJECT_DIR="$2"; shift 2 ;;
        --help)
            echo "Usage: bash install.sh [--lang en|es] [--dir /path/to/project]"
            exit 0
            ;;
        *)        shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}!${RESET} $1"; }
err()  { echo -e "  ${RED}✗${RESET} $1" >&2; }
info() { echo -e "  ${DIM}·${RESET} $1"; }
sep()  { echo -e "${DIM}────────────────────────────────────────────────────────${RESET}"; }
header() {
    echo
    sep
    echo -e "  ${BOLD}${CYAN}PRAXIS${RESET} ${BOLD}$1${RESET}"
    sep
}

# ---------------------------------------------------------------------------
# Check Python
# ---------------------------------------------------------------------------
check_python() {
    local python_cmd=""

    for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8; do
        if command -v "$cmd" &>/dev/null; then
            version=$("$cmd" -c "import sys; print(sys.version_info[:2])" 2>/dev/null || echo "(0, 0)")
            major=$(echo "$version" | tr -d '()' | cut -d',' -f1 | tr -d ' ')
            minor=$(echo "$version" | tr -d '()' | cut -d',' -f2 | tr -d ' ')
            if [[ "$major" -ge 3 && "$minor" -ge 8 ]]; then
                python_cmd="$cmd"
                break
            fi
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        err "Python 3.8+ is required but not found."
        info "Install Python: https://python.org/downloads"
        exit 1
    fi

    echo "$python_cmd"
}

# ---------------------------------------------------------------------------
# Main installation
# ---------------------------------------------------------------------------
main() {
    header "Universal Kit v${PRAXIS_VERSION} — Installer"
    echo

    # Check Python
    info "Checking Python version..."
    PYTHON=$(check_python)
    PYTHON_VERSION=$("$PYTHON" --version 2>&1)
    ok "Found: $PYTHON_VERSION ($PYTHON)"

    # Show consent file
    echo
    if [[ "$LANG" == "es" && -f "$SCRIPT_DIR/CONSENTIMIENTO.md" ]]; then
        CONSENT_FILE="$SCRIPT_DIR/CONSENTIMIENTO.md"
    else
        CONSENT_FILE="$SCRIPT_DIR/CONSENT.md"
    fi

    if [[ -f "$CONSENT_FILE" ]]; then
        echo -e "  ${BOLD}Research Consent Form:${RESET}"
        info "Please review: $CONSENT_FILE"
        echo
        # Show first 20 lines of consent
        head -20 "$CONSENT_FILE" | sed 's/^/    /'
        echo
        info "(See full file for complete terms)"
    fi

    echo
    read -rp "  Do you consent to participate in this research? [y/N]: " consent_response
    echo
    consent_lower="${consent_response,,}"
    if [[ "$consent_lower" != "y" && "$consent_lower" != "yes" && \
          "$consent_lower" != "s" && "$consent_lower" != "si" ]]; then
        warn "Consent required to participate. Exiting."
        info "Read $CONSENT_FILE for full research details."
        exit 0
    fi

    ok "Consent recorded."

    # Set up project directory
    echo
    info "Project directory: $PROJECT_DIR"
    if [[ ! -d "$PROJECT_DIR" ]]; then
        mkdir -p "$PROJECT_DIR"
        ok "Created: $PROJECT_DIR"
    fi

    # Detect platforms
    echo
    info "Detecting AI platforms..."
    "$PYTHON" -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/collector')
from praxis_collector import detect_platforms
import os
os.chdir('$PROJECT_DIR')
platforms = detect_platforms()
if platforms:
    print('  Detected: ' + ', '.join(platforms))
else:
    print('  No specific platforms detected — will use generic adapter')
" 2>/dev/null || info "Platform detection skipped."

    # Initialize PRAXIS
    echo
    info "Initializing PRAXIS..."
    cd "$PROJECT_DIR"
    "$PYTHON" "$SCRIPT_DIR/collector/praxis_cli.py" init \
        --lang "$LANG" \
        --dir "$PROJECT_DIR"

    EXIT_CODE=$?
    if [[ $EXIT_CODE -ne 0 ]]; then
        err "Initialization failed (exit code $EXIT_CODE)."
        exit $EXIT_CODE
    fi

    # Set up praxis command alias
    echo
    _setup_alias "$PYTHON" "$SCRIPT_DIR"

    # Final instructions
    echo
    sep
    echo -e "  ${BOLD}${GREEN}Installation complete!${RESET}"
    sep
    echo
    if [[ "$LANG" == "es" ]]; then
        info "Próximos pasos:"
        info "  1. Completa la encuesta inicial:  praxis survey pre"
        info "  2. Registra tus tareas de IA:     praxis log 'lo que hiciste' -d <min> -m <modelo>"
        info "  3. Activa PRAXIS tras 7 días:     praxis activate"
        info "  4. Verifica tu progreso:          praxis status"
    else
        info "Next steps:"
        info "  1. Complete the pre-survey:  praxis survey pre"
        info "  2. Log your AI tasks daily:  praxis log 'what you did' -d <min> -m <model>"
        info "  3. After 7+ days, activate:  praxis activate"
        info "  4. Check your progress:      praxis status"
    fi
    echo
}

_setup_alias() {
    local python="$1"
    local script_dir="$2"
    local cli_path="$script_dir/collector/praxis_cli.py"

    # Create a wrapper script
    local bin_dir="$HOME/.local/bin"
    mkdir -p "$bin_dir"
    local wrapper="$bin_dir/praxis"

    cat > "$wrapper" << WRAPPER
#!/usr/bin/env bash
"$python" "$cli_path" "\$@"
WRAPPER
    chmod +x "$wrapper"

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
        warn "Add to your PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
        info "Then restart your terminal or run: source ~/.bashrc"
        info "Or call directly: python $cli_path <command>"
    else
        ok "Command 'praxis' installed to $bin_dir"
    fi
}

main "$@"
