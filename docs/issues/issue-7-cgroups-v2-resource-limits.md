# [Professional Feature] feat(cgroups): Linux cgroups v2 Kernel-Level Resource Enforcement

**Labels**: `feature`, `linux`, `cgroups`, `resources`, `control-plane`  
**Target Files**: `src/formicx/resources/cgroups.py`, `src/formicx/models/agent.py`

## Overview
Elevate Phase 8 Resource Monitoring to **Phase 9 Resource Control** using Linux Control Groups (`cgroups v2`). Attach running agent PIDs to Linux kernel cgroup hierarchies under `/sys/fs/cgroup/formicx/<agent_id>/`.

## Features
- **Hard Memory Limits**: Enforce `memory.max` (e.g. 512MB RAM) preventing rogue agents from exhausting host RAM.
- **CPU Quota Capping**: Enforce `cpu.max` (e.g. max 50% CPU allocation).
- **IO Weighting**: Set `io.weight` to prioritize disk IO between competing agents.

## Manifest Configuration Example
```yaml
resources:
  cpu_limit: "50%"
  memory_limit: "512MB"
```

## Acceptance Criteria
- [ ] Implement `CGroupManager` abstraction interacting with `/sys/fs/cgroup`.
- [ ] Gracefully fall back to monitoring-only mode on systems without cgroups v2 enabled (e.g., Windows development).
- [ ] Add unit tests and integration tests for cgroup creation and enforcement.
