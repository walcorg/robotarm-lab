# MCP tools

Server name: `robotarm-lab`. Implemented in `src/robotarm_lab/server.py`.

Every action tool returns:

```json
{ "ok": true, "code": "ok", "message": "C03 placed in station 3.", "scene": { ... } }
```

`scene` is always the state **after** the action, so Claude never needs a second call to see what
happened.

## Tools

| Tool | Arguments | Purpose |
|------|-----------|---------|
| `get_workcell` | – | Stations (id, label) and which stations each hand reaches. Call once per session. |
| `get_scene` | – | Objects per station, hand states, stop flag. |
| `move_object` | `hand`, `from_station`, `to_station` | Pick, place and return home. Validated before any motion. Preferred for simple transfers. |
| `pick` | `hand`, `station` | Grasp only. Used for hand-overs and multi-step tasks. |
| `place` | `hand`, `station` | Release the held object into an empty station. |
| `bring_tube` | `tube`, `hand` (optional) | Turn the reel forward until `tube` faces the arms. See [reel indexing](design/reel-indexing.md). |
| `rotate_reel` | `hand`, `steps` (1–11) | Advance the reel an exact number of positions. Forward only. |
| `home` | `hand` | Return to home pose, keep the held object. |
| `stop` | – | Halt all motion; latches. |
| `reset` | – | Clear a software stop. Only after the human confirms. |
| `recent_actions` | `n` (default 20) | Action log with result codes. |

Planned for phase 1:

| Tool | Purpose |
|------|---------|
| `capture` | Annotated JPEG from the overhead camera (boxes + ids), for ambiguous scenes |
| `run_skill` | Run a named trained skill (`pour`, `open_lid`) at a station |

## Result codes

| Code | Meaning | Expected reaction |
|------|---------|-------------------|
| `ok` | Done | Continue |
| `grip_failed` | Hand closed but nothing is held; object still in its station | Check scene, retry once, then ask the human |
| `station_empty` | No object where one was expected | Re-read scene; the plan is stale |
| `station_occupied` | Target station not free | Choose another station or clear it first |
| `hand_busy` | Hand already holds something | Place it first |
| `hand_empty` | `place` without holding anything | Re-read scene |
| `unreachable` | Station outside that hand's reach | Use the other hand or a hand-over via the shared station |
| `arms_not_clear` | A hand is not at home while the reel should turn | Send both hands home, then retry |
| `latch_failed` | Reel latch did not seat after a step; reel is unlocked | Rotate one more step to seat it; if it fails again, stop and ask |
| `reel_unlatched` | Station work refused because the reel is not locked | Seat the latch first (`rotate_reel` 1 step) |
| `no_reel` | This workcell has no reel | Do not use reel tools |
| `estopped` | Cell is stopped | Tell the human; do not call `reset` on your own |
| `invalid_argument` | Unknown hand or station | Fix the call |
| `backend_error` | Hardware or policy fault | Stop and report |

## Registering with Claude Code

```bash
claude mcp add robotarm -- robotarm-mcp --backend sim
```
