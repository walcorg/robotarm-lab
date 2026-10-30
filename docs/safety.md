# Safety

The robot must be safe when any software layer above the firmware is wrong, slow or gone.
That includes Claude, the network, the MCP server and the learned policy.

## Who owns what

| Mechanism | Layer | Notes |
|-----------|-------|-------|
| Hardware e-stop (mushroom button) | Power stage | Cuts actuator power, independent of every MCU |
| Joint position limits | Firmware | Hard-coded per joint, below mechanical stops |
| Current / torque limits | Firmware | Per joint; fingers limited lower than shoulders |
| Command watchdog | Firmware | No valid frame for 100 ms → ramp to hold |
| Thermal cut-back | Firmware | Per motor driver |
| Self-collision zones | Firmware (phase 3) | Simple capsule check between the two arms |
| Reachability, occupancy | MCP server | Rejects impossible plans before motion |
| Software stop | MCP server → firmware | `stop` tool; latches until a human-approved `reset` |
| Task judgment | Claude | Stops when the scene looks wrong; asks the human |

## Rules for the planner

- Claude never calls `reset` on its own initiative; a human confirms the cell is clear first.
- `unreachable` and `estopped` are final for that request. No workaround through other tools.
- After two consecutive failures on the same step, stop and ask.

## Bring-up checklist (each new arm)

- [ ] E-stop cuts power to all joints with the MCU still running
- [ ] Each joint stops at its soft limit before the mechanical stop
- [ ] Current limit trips on a stalled joint within 200 ms
- [ ] Unplugging USB / CAN puts the arm in hold within 100 ms
- [ ] Power loss does not drop a held object onto a person (brake or non-backdrivable wrist)
