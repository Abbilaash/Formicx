# [Professional Feature] feat(systemd): Native Linux systemd service supervision and journald logging

**Labels**: `feature`, `linux`, `systemd`, `os-integration`  
**Target Files**: `src/formicx/core/systemd/`, `src/formicx/cli/commands/agent.py`

## Overview
Bind Formicx agents directly to Linux `systemd` user/system service units. Instead of managing agent subprocesses purely in Python memory, Formicx generates `systemd` unit files (`formicx-agent@<agent_id>.service`).

## Key Benefits
- **Boot Persistence**: Formicx agents auto-start on Linux system boot via `systemctl enable`.
- **Kernel-Level Supervision**: `systemd` handles process auto-restart on unexpected crashes.
- **Unified OS Logging**: Agent standard output and errors log directly into Linux `journald` (`journalctl -u formicx-agent@research-agent`).

## Acceptance Criteria
- [ ] Add `formicx agent export-systemd <agent>` command generating valid `systemd` unit files.
- [ ] Support systemd service unit management via `formicxd` systemd integration mode.
- [ ] Add documentation in `docs/architecture/systemd-integration.md`.
