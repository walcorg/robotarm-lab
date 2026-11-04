"""MCP server exposing the workcell to Claude.

Run with the simulated backend:
    robotarm-mcp --backend sim
Register it in Claude Code:
    claude mcp add robotarm -- robotarm-mcp --backend sim
"""
from __future__ import annotations

import argparse
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .backends import SimBackend
from .controller import Controller
from .workcell import Workcell

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "workcell.toml"

INSTRUCTIONS = """\
You plan tasks for a dual-arm workcell. Objects only sit in numbered stations.
Call get_workcell once to learn which hand reaches which station, and get_scene before acting.
Prefer move_object for simple transfers. The cultivation reel has no motor: use bring_tube to
have the arms turn it; it only turns forward and is latched at every position.
Every action returns a result code and the new scene;
read it before the next step. On grip_failed, look at the scene and decide whether to retry once
or ask the human. Call stop immediately if anything looks unsafe. You are not the safety layer:
the firmware enforces limits, but never try to work around a stop or an unreachable result."""


def build_server(controller: Controller) -> MCPServer:
    server = MCPServer("robotarm-lab", instructions=INSTRUCTIONS, version="0.1.0")

    @server.tool()
    def get_workcell() -> dict:
        """Stations (id and label) and which stations each hand can reach."""
        return controller.workcell()

    @server.tool()
    def get_scene() -> dict:
        """Current objects per station, what each hand holds, and whether the cell is stopped."""
        return controller.scene()

    @server.tool()
    def move_object(hand: str, from_station: int, to_station: int) -> dict:
        """Move the object in from_station to to_station with one hand ('left' or 'right'),
        then return that hand home. Nothing moves if the plan is impossible."""
        return controller.move_object(hand, from_station, to_station).to_dict()

    @server.tool()
    def pick(hand: str, station: int) -> dict:
        """Grasp the object in a station. Use for hand-overs; prefer move_object otherwise."""
        return controller.pick(hand, station).to_dict()

    @server.tool()
    def place(hand: str, station: int) -> dict:
        """Release the held object into an empty station."""
        return controller.place(hand, station).to_dict()

    @server.tool()
    def bring_tube(tube: int, hand: str | None = None) -> dict:
        """Turn the cultivation reel forward until `tube` (1-12) faces the arms. The arms turn
        it themselves; both hands must be at home and the operating hand empty."""
        return controller.bring_tube(tube, hand).to_dict()

    @server.tool()
    def rotate_reel(hand: str, steps: int) -> dict:
        """Advance the reel a number of positions with one hand. Forward only (ratchet).
        Prefer bring_tube unless you need an exact number of steps."""
        return controller.rotate_reel(hand, steps).to_dict()

    @server.tool()
    def home(hand: str) -> dict:
        """Return a hand to its home pose without releasing what it holds."""
        return controller.home(hand).to_dict()

    @server.tool()
    def stop() -> dict:
        """Halt all motion immediately. Latches until reset."""
        return controller.stop().to_dict()

    @server.tool()
    def reset() -> dict:
        """Clear a software stop. Only call after the human confirms the cell is safe."""
        return controller.reset().to_dict()

    @server.tool()
    def recent_actions(n: int = 20) -> list[dict]:
        """The last n actions with their result codes."""
        return controller.recent_actions(n)

    return server


def make_controller(backend: str, config: str | Path, grip_fail_rate: float = 0.0,
                    latch_fail_rate: float = 0.0) -> Controller:
    wc = Workcell.load(config)
    if backend == "sim":
        return Controller(SimBackend(wc, grip_fail_rate=grip_fail_rate,
                                     latch_fail_rate=latch_fail_rate), wc)
    raise SystemExit(f"Backend '{backend}' is not implemented yet (see docs/roadmap.md).")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="robotarm-lab MCP server")
    ap.add_argument("--backend", default="sim", choices=["sim", "so101", "custom"])
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--grip-fail-rate", type=float, default=0.0,
                    help="simulation only: probability that a grasp fails")
    ap.add_argument("--latch-fail-rate", type=float, default=0.0,
                    help="simulation only: probability that the reel latch does not seat")
    a = ap.parse_args(argv)
    build_server(make_controller(a.backend, a.config, a.grip_fail_rate, a.latch_fail_rate)).run("stdio")


if __name__ == "__main__":
    main()
