# Roadmap

Each phase has an exit criterion that is measurable, so the next phase starts from something
that works.

## Phase 0: Specs and simulated cell
- Repository, architecture, MCP tool spec, scene schema, safety rules
- MCP server with simulated backend and tests

**Exit:** Claude completes a multi-step task (including a hand-over) against the simulated cell
and recovers from injected grip failures.

## Phase 1: Pipeline validation on SO-101
- Build two LeRobot SO-101 follower arms + one leader arm, overhead camera, two wrist cameras
- Five stations on a rail with ArUco markers and chamfered guides
- `so101` backend: `pick` / `place` / `home` as trained skills
- `capture` tool with annotated image

**Exit:** 20 consecutive `move_object` calls between stations with ≥ 90 % success, planned by
Claude.

## Phase 2: Datasets and policy training
- Teleoperate and record ≥ 50 episodes per skill, pushed to the Hugging Face Hub
- Fine-tune SmolVLA (and compare with ACT) on a rented or local modern NVIDIA GPU
- Policy cards in `policy/` with success rates per skill

**Exit:** each skill ≥ 90 % success over 30 trials on the SO-101 cell.

## Phase 3: Custom arms and hands
- Arm and hand design in Autodesk Inventor (`hardware/`), tendon-driven fingers
- Joint encoders on every axis, current sensing on every finger, wrist camera mount
- Firmware: 1 kHz PID, limits, watchdog, e-stop input
- `custom` backend; retrain skills on the new embodiment

**Exit:** safety bring-up checklist passes on both arms; one skill transferred at ≥ 80 % success.

## Phase 4: Integration
- Claude plans real tasks on the custom cell (sorting, hand-overs, lab routines)
- Visualization driven by live data instead of a scripted timeline

**Exit:** a 10-step task completed unattended with logs that explain every decision.
