# Hardware

Licensed under [CERN-OHL-W-2.0](../LICENSE-HARDWARE): if you modify these designs and distribute
the result, you share the modified design files.

| Folder | Contents |
|--------|----------|
| `arms/` | Shoulder-to-wrist structure, joint modules |
| `hands/` | Tendon-driven fingers, palm, wrist interface |
| `workcell/` | Rail, stations (chamfered nests with ArUco marker pads), camera mast |

## Conventions

- Source: Autodesk Inventor (`.ipt`, `.iam`). Commit an export next to every source:
  `.step` for assemblies and parts, `.stl` / `.3mf` for printed parts.
- Name parts `<subsystem>-<part>-v<major>` (e.g. `hand-finger-proximal-v1.ipt`).
- Every assembly has a `BOM.csv` with: part, qty, material, process (print / CNC / bought),
  supplier part number.
- Units: millimetres. Robot base frame: x along the rail, y away from the arms, z up.
- Large binaries go through Git LFS (`*.ipt`, `*.iam`, `*.step`, `*.stl`).

## Requirements for the custom arms

- Measured position on every joint (absolute encoder or servo with feedback)
- Current sensing on every finger actuator, to detect grasps
- Wrist camera mount with a fixed, calibrated pose
- Non-backdrivable or braked wrist so a held object is not dropped on power loss
- Mechanical stops beyond the firmware soft limits

## Requirements for the reel

See [docs/design/reel-indexing.md](../docs/design/reel-indexing.md): indexing plate with 12
notches and a spring latch, 12 hub pegs, ratchet and pawl, latch-seated switch, tube-position
sensor. No reel motor.
