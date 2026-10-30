# Architecture

## Layers

| # | Layer | Runs on | Rate | Owns | Must never |
|---|-------|---------|------|------|------------|
| 1 | Claude (planner) | Anthropic servers | 1 decision per 1–3 s | Task choice, sequencing, recovery, talking to the human | Be in a control loop; bypass a stop |
| 2 | Network | Internet (Starlink at home) | 50–200 ms RTT, drops of 5–15 s | Transport | Be assumed reliable |
| 3 | MCP server (`src/robotarm_lab`) | Local PC | < 5 ms per call | Validation, scene assembly, action log | Move anything that failed validation |
| 4 | Policy (LeRobot: SmolVLA / ACT) | Local GPU PC | ~30 Hz | Turning one skill into joint trajectories from camera + joint state | Exceed the joint envelope (firmware clamps anyway) |
| 5 | Firmware | MCU per arm | ~1 kHz | PID per joint, current and position limits, watchdog, e-stop | Trust any upstream command blindly |
| 6 | Actuators | Servos / BLDC + encoders | PWM 50–330 Hz | Torque, measured position | — |

The design rule is that **each layer only issues commands to the layer directly below and only
trusts what that layer measures**. Claude never sends joint angles; the policy never decides
which object to move.

## Timing budget for one `move_object`

| Step | Time |
|------|------|
| Scene JSON (+ optional image) to Claude | 0.2–0.5 s |
| Claude reads, decides, writes the tool call | 1–3 s |
| Tool call reaches MCP server | 0.05–0.2 s |
| Validation + dispatch | < 5 ms |
| Policy executes pick → place → home | 3–8 s at 30 Hz |
| Result + scene back to Claude | 0.05–0.2 s |

The network and Claude only appear twice per task, so a 10 s Starlink drop pauses planning
but never leaves an arm without control: the policy and firmware finish or hold.

## Interfaces

### Claude ↔ MCP server
MCP over stdio (Claude Code on the local PC) or streamable HTTP. Tools and result codes:
[mcp-tools.md](mcp-tools.md). Scene format: [scene-schema.md](scene-schema.md).

### MCP server ↔ backend
Python `Backend` ABC in `src/robotarm_lab/backends/base.py`: `scene`, `pick`, `place`, `home`,
`stop`, `reset`, `capture`. A backend executes exactly one primitive and reports what physically
happened. Implementations:

| Backend | Phase | Notes |
|---------|-------|-------|
| `sim` | 0 | Deterministic, optional random grip failures |
| `so101` | 1 | LeRobot SO-101 follower arms; skills = trained policies per primitive |
| `custom` | 3–4 | Custom arms and hands; same skills retrained on new embodiment |

### Policy ↔ firmware (draft)
Binary frames over USB-CDC or CAN-FD at the policy rate:

| Field | Type | Notes |
|-------|------|-------|
| `seq` | u16 | Monotonic; firmware drops out-of-order frames |
| `mode` | u8 | 0 hold, 1 position, 2 current-limited position |
| `targets[n]` | i16 | Joint targets in 0.01° |
| `max_current[n]` | u16 | mA, clamped again by firmware limits |
| `crc` | u16 | CRC-16/CCITT |

Firmware replies with measured position, current, temperature and a fault bitfield per joint.
If no valid frame arrives for 100 ms the firmware ramps to *hold*.

### Perception
- Fixed overhead camera: YOLO detections + ArUco markers on each station → station occupancy and
  object ids in the scene JSON.
- Wrist cameras (one per hand): input to the policy only; never sent to Claude.
- Claude receives an image only when it asks (`capture`, phase 1) or when the scene is ambiguous.

## Why stations

Free-form manipulation spends most of its error budget estimating where an object is and how it
is oriented. Stations remove that: each one has a known approach pose, chamfered guides that
centre the object and a marker for calibration. The camera's job becomes *verification*
(is the object there, is it upright), which is far more reliable than *estimation*.
