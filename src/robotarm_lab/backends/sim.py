"""Deterministic simulated workcell, for developing the MCP layer before hardware exists."""
from __future__ import annotations

import random
import time

from ..scene import ActionResult, HandState, ObjectState, Scene
from ..workcell import Workcell
from .base import Backend


class SimBackend(Backend):
    def __init__(self, workcell: Workcell, grip_fail_rate: float = 0.0,
                 seed: int | None = 0, step_delay_s: float = 0.0):
        self.wc = workcell
        self.grip_fail_rate = grip_fail_rate
        self.rng = random.Random(seed)
        self.step_delay_s = step_delay_s
        self.estopped = False
        self.objects = {o.id: ObjectState(o.id, o.cls, o.station) for o in workcell.initial_objects}
        self.hands = {name: HandState(name) for name in workcell.hands}

    # ---- helpers ---------------------------------------------------------
    def _wait(self):
        if self.step_delay_s:
            time.sleep(self.step_delay_s)

    def _at(self, station: int) -> ObjectState | None:
        return next((o for o in self.objects.values() if o.station == station), None)

    def _result(self, ok: bool, code: str, message: str) -> ActionResult:
        return ActionResult(ok, code, message, self.scene().to_dict())

    # ---- Backend ---------------------------------------------------------
    def scene(self) -> Scene:
        return Scene(time.time(), self.estopped,
                     [ObjectState(**vars(o)) for o in self.objects.values()],
                     [HandState(**vars(h)) for h in self.hands.values()])

    def pick(self, hand: str, station: int) -> ActionResult:
        if self.estopped:
            return self._result(False, "estopped", "Stopped; call reset first.")
        h = self.hands[hand]
        obj = self._at(station)
        h.at_station = station
        self._wait()
        if obj is None:
            return self._result(False, "station_empty", f"Station {station} is empty.")
        if self.rng.random() < self.grip_fail_rate:
            h.grip = "closed"
            return self._result(False, "grip_failed",
                                f"Closed on nothing at station {station}; {obj.id} is still there.")
        obj.station, obj.held_by = None, hand
        h.grip, h.holding = "holding", obj.id
        return self._result(True, "ok", f"{hand} hand holds {obj.id}.")

    def place(self, hand: str, station: int) -> ActionResult:
        if self.estopped:
            return self._result(False, "estopped", "Stopped; call reset first.")
        h = self.hands[hand]
        if h.holding is None:
            return self._result(False, "hand_empty", f"{hand} hand is not holding anything.")
        if self._at(station) is not None:
            return self._result(False, "station_occupied", f"Station {station} is occupied.")
        h.at_station = station
        self._wait()
        obj = self.objects[h.holding]
        obj.station, obj.held_by = station, None
        h.grip, h.holding = "open", None
        return self._result(True, "ok", f"{obj.id} placed in station {station}.")

    def home(self, hand: str) -> ActionResult:
        if self.estopped:
            return self._result(False, "estopped", "Stopped; call reset first.")
        h = self.hands[hand]
        h.at_station = None
        if h.holding is None:
            h.grip = "open"
        self._wait()
        return self._result(True, "ok", f"{hand} hand at home.")

    def stop(self) -> ActionResult:
        self.estopped = True
        return self._result(True, "ok", "All motion stopped.")

    def reset(self) -> ActionResult:
        self.estopped = False
        return self._result(True, "ok", "Stop cleared.")
