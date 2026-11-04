import asyncio
from pathlib import Path

import pytest

from robotarm_lab.backends import SimBackend
from robotarm_lab.controller import Controller
from robotarm_lab.server import build_server
from robotarm_lab.workcell import Workcell

CONFIG = Path(__file__).resolve().parents[1] / "config" / "workcell.toml"


def make(**kw):
    wc = Workcell.load(CONFIG)
    return Controller(SimBackend(wc, **kw), wc)


@pytest.fixture
def ctl():
    return make()


def reel(ctl):
    return ctl.scene()["reel"]


def test_scene_reports_reel(ctl):
    assert reel(ctl) == {"positions": 12, "tube_at_work": 1, "latched": True}


def test_bring_tube_forward(ctl):
    r = ctl.bring_tube(7)
    assert r.ok
    assert reel(ctl)["tube_at_work"] == 7 and reel(ctl)["latched"]
    assert ctl.recent_actions()[-1]["args"]["steps"] == 6


def test_bring_tube_wraps_forward_only(ctl):
    ctl.bring_tube(11)
    ctl.bring_tube(2)  # ratchet: 11 -> 12 -> 1 -> 2, never backwards
    assert reel(ctl)["tube_at_work"] == 2
    assert ctl.recent_actions()[-1]["args"]["steps"] == 3


def test_bring_tube_already_there(ctl):
    r = ctl.bring_tube(1)
    assert r.ok and "already" in r.message


def test_reel_needs_arms_clear(ctl):
    ctl.pick("left", 2)  # left hand now holds the cup at station 2
    assert ctl.rotate_reel("left", 1).code == "hand_busy"
    assert ctl.rotate_reel("right", 1).code == "arms_not_clear"
    assert reel(ctl)["tube_at_work"] == 1


def test_steps_must_be_forward_and_less_than_a_turn(ctl):
    assert ctl.rotate_reel("left", 0).code == "invalid_argument"
    assert ctl.rotate_reel("left", -1).code == "invalid_argument"
    assert ctl.rotate_reel("left", 12).code == "invalid_argument"


def test_reel_blocked_while_stopped(ctl):
    ctl.stop()
    assert ctl.bring_tube(5).code == "estopped"


def test_latch_failure_stops_rotation_and_blocks_station_work():
    ctl = make(latch_fail_rate=1.0)
    r = ctl.bring_tube(5)
    assert r.code == "latch_failed"
    assert reel(ctl)["tube_at_work"] == 2 and not reel(ctl)["latched"]
    assert ctl.move_object("left", 2, 3).code == "reel_unlatched"


def test_server_exposes_reel_tools(ctl):
    names = {t.name for t in asyncio.run(build_server(ctl).list_tools())}
    assert {"bring_tube", "rotate_reel"} <= names
