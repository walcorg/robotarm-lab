# Firmware

Joint controller firmware for the custom arms (phase 3). The SO-101 arms in phase 1 use their
stock Feetech servo firmware through LeRobot.

## Requirements

| ID | Requirement |
|----|-------------|
| FW-1 | Position PID per joint at ≥ 1 kHz |
| FW-2 | Hard position limits per joint, stored in flash, not settable from the host |
| FW-3 | Current limit per joint; stall detection trips within 200 ms |
| FW-4 | Watchdog: no valid command frame for 100 ms → ramp to hold |
| FW-5 | E-stop input latches a fault; clearing requires the button released and a reset command |
| FW-6 | Telemetry at the command rate: position, current, temperature, fault bits per joint |
| FW-7 | Command frames carry a sequence number and CRC; invalid frames are dropped and counted |

Frame format: see [docs/architecture.md](../docs/architecture.md#policy--firmware-draft).

## Candidate platform

STM32G4 (FPU, CORDIC, FDCAN) per arm, CAN-FD between arms and host adapter. To be confirmed in
phase 3.
