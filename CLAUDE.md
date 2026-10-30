# robotarm-lab: notes for Claude

- Everything committed to this repository is in English (code, comments, docs, commit messages).
- Brand: write "WALCORG" in prose, "walcorg" in identifiers and URLs.
- Claude is the planner, never the controller. Do not add tools that send joint angles,
  velocities or raw coordinates to the robot; add skills or station-level primitives instead.
- Safety limits belong in firmware (`firmware/`), never only in Python. The MCP controller may
  add checks but must not be the only line of defense.
- Keep `docs/mcp-tools.md` and `docs/scene-schema.md` in sync with `src/robotarm_lab/`.
- Run `pytest -q` before committing.
- Hardware files are CERN-OHL-W-2.0; software is MIT.
