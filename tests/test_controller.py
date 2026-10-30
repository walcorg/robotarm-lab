import asyncio
from pathlib import Path

import pytest

from robotarm_lab.backends import SimBackend
from robotarm_lab.controller import Controller
from robotarm_lab.server import build_server
from robotarm_lab.workcell import Workcell

CONFIG = Path(__file__).resolve().parents[1] / "config" / "workcell.toml"


@pytest.fixture
def ctl():
    wc = Workcell.load(CONFIG)
    return Controller(SimBackend(wc), wc)


def where(ctl, obj_id):
    return next(o for o in ctl.scene()["objects"] if o["id"] == obj_id)["station"]


def test_move_object_happy_path(ctl):
    r = ctl.move_object("left", 2, 3)
    assert r.ok and r.code == "ok"
    assert where(ctl, "C03") == 3
    left = next(h for h in r.scene["hands"] if h["name"] == "left")
    assert left["holding"] is None and left["at_station"] is None


def test_unreachable_station_moves_nothing(ctl):
    r = ctl.move_object("left", 2, 5)
    assert not r.ok and r.code == "unreachable"
    assert where(ctl, "C03") == 2


def test_occupied_target_rejected_before_motion(ctl):
    ctl.move_object("left", 2, 3)
    r = ctl.move_object("right", 4, 3)
    assert r.code == "station_occupied"
    assert where(ctl, "V01") == 4


def test_handover_through_shared_station(ctl):
    assert ctl.move_object("left", 2, 3).ok
    assert ctl.move_object("right", 3, 5).ok
    assert where(ctl, "C03") == 5


def test_stop_latches_until_reset(ctl):
    ctl.stop()
    assert ctl.move_object("left", 2, 3).code == "estopped"
    ctl.reset()
    assert ctl.move_object("left", 2, 3).ok


def test_grip_failure_leaves_object_and_homes_hand():
    wc = Workcell.load(CONFIG)
    ctl = Controller(SimBackend(wc, grip_fail_rate=1.0), wc)
    r = ctl.move_object("left", 2, 3)
    assert r.code == "grip_failed"
    assert where(ctl, "C03") == 2
    assert ctl.recent_actions()[-1]["code"] == "grip_failed"


def test_invalid_hand(ctl):
    assert ctl.pick("middle", 2).code == "invalid_argument"


def test_pick_place_and_busy_hand(ctl):
    assert ctl.pick("left", 2).ok
    assert ctl.pick("left", 1).code == "hand_busy"
    assert ctl.place("left", 1).ok
    assert where(ctl, "C03") == 1


def test_server_exposes_tools(ctl):
    tools = asyncio.run(build_server(ctl).list_tools())
    names = {t.name for t in tools}
    assert {"get_workcell", "get_scene", "move_object", "pick", "place",
            "home", "stop", "reset", "recent_actions"} <= names
