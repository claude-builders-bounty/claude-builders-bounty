#!/usr/bin/env bash
# hermes_cua_env.sh — Setup HERMES_CUA_DRIVER_CMD for WSL2 interop
# Source this in ~/.profile AND add to hermes-gateway systemd drop-in

set -euo pipefail

# ============================================================================
# CONFIGURATION — EDIT THESE FOR YOUR MACHINE
# ============================================================================
WINDOWS_USER="Administrator"  # Windows username
CUA_DRIVER_RELATIVE_PATH="AppData/Local/Programs/Cua/cua-driver/bin/cua-driver.exe"
# ============================================================================

# Derive the WSL2 path to the Windows binary
CUA_DRIVER_WIN_PATH="/mnt/c/Users/${WINDOWS_USER}/${CUA_DRIVER_RELATIVE_PATH}"

# Verify the binary exists
if [[ ! -f "${CUA_DRIVER_WIN_PATH}" ]]; then
    echo "ERROR: cua-driver not found at ${CUA_DRIVER_WIN_PATH}" >&2
    echo "Check WINDOWS_USER and CUA_DRIVER_RELATIVE_PATH in this script." >&2
    exit 1
fi

export HERMES_CUA_DRIVER_CMD="${CUA_DRIVER_WIN_PATH}"
echo "HERMES_CUA_DRIVER_CMD set to: ${HERMES_CUA_DRIVER_CMD}"

# ============================================================================
# USAGE
# ============================================================================
# 1. For interactive shells: source this in ~/.profile
#    echo 'source /path/to/hermes_cua_env.sh' >> ~/.profile
#
# 2. For systemd service (Hermes Gateway):
#    mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
#    cat > ~/.config/systemd/user/hermes-gateway.service.d/cua-driver.conf <<'EOF'
#    [Service]
#    Environment=HERMES_CUA_DRIVER_CMD=/mnt/c/Users/Administrator/AppData/Local/Programs/Cua/cua-driver/bin/cua-driver.exe
#    EOF
#    systemctl --user daemon-reload
#    systemctl --user restart hermes-gateway
#
# 3. Verify:
#    hermes computer-use status
# ============================================================================

# If run directly (not sourced), just print the export line for copy-paste
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "export HERMES_CUA_DRIVER_CMD=\"${HERMES_CUA_DRIVER_CMD}\""
fi