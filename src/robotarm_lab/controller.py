"""Validation layer between the MCP tools and a backend.

Rejects requests that cannot be right (unknown hand, unreachable or occupied station,
hand already busy) before any motor moves, and keeps an action log Claude can read.
It does not retry on its own: a failed grip is reported, and the planner decides.
"""
from __future__ import annotations

import time
from collections import deque

from .backends.base import Backend
from .scene import ActionResult
from .workcell import Workcell


class Controller:
    def __init__(self, backend: Backend, workcell: Workcell, log_size: int = 200):
        self.backend = backend
        self.wc = workcell
        self.log: deque[dict] = deque(maxlen=log_size)

    # ---- helpers ---------------------------------------------------------
    def _reject(self, code: str, message: str) -> ActionResult:
        return ActionResult(False, code, message, self.backend.scene().to_dict())

    def _check_hand(self, hand: str) -> ActionResult | None:
        if hand not in self.wc.hands:
            return self._reject("invalid_argument", f"Unknown hand '{hand}'. Use one of {sorted(self.wc.hands)}.")
        if self.backend.scene().estopped:
            return self._reject("estopped", "Stopped; call reset first.")
        return None

    def _check_station(self, hand: str, station: int) -> ActionResult | None:
        if station not in self.wc.stations:
            return self._reject("invalid_argument", f"Unknown station {station}.")
        if not self.wc.can_reach(hand, station):
            reach = sorted(self.wc.hands[hand].reach)
            return self._reject("unreachable", f"The {hand} hand cannot reach station {station}; it reaches {reach}.")
        return None

    def _check_reel_locked(self) -> ActionResult | None:
        sc = self.backend.scene()
        if sc.reel is not None and not sc.reel.latched:
            return self._reject("reel_unlatched",
                                "The reel is not latched; seat the latch before working at a station.")
        return None

    def _record(self, action: str, args: dict, result: ActionResult) -> ActionResult:
        self.log.append({"t": time.time(), "action": action, "args": args,
                         "ok": result.ok, "code": result.code, "message": result.message})
        return result

    # ---- operations ------------------------------------------------------
    def scene(self) -> dict:
        return self.backend.scene().to_dict()

    def workcell(self) -> dict:
        return {
            "name": self.wc.name,
            "stations": [{"id": s.id, "label": s.label} for s in self.wc.stations.values()],
            "hands": {h.name: {"reach": sorted(h.reach)} for h in self.wc.hands.values()},
        }

    def pick(self, hand: str, station: int) -> ActionResult:
        args = {"hand": hand, "station": station}
        if err := self._check_hand(hand) or self._check_station(hand, station) or self._check_reel_locked():
            return self._record("pick", args, err)
        sc = self.backend.scene()
        if sc.hand(hand).holding:
            return self._record("pick", args, self._reject("hand_busy", f"The {hand} hand already holds {sc.hand(hand).holding}."))
        if sc.object_at(station) is None:
            return self._record("pick", args, self._reject("station_empty", f"Station {station} is empty."))
        return self._record("pick", args, self.backend.pick(hand, station))

    def place(self, hand: str, station: int) -> ActionResult:
        args = {"hand": hand, "station": station}
        if err := self._check_hand(hand) or self._check_station(hand, station) or self._check_reel_locked():
            return self._record("place", args, err)
        sc = self.backend.scene()
        if not sc.hand(hand).holding:
            return self._record("place", args, self._reject("hand_empty", f"The {hand} hand is not holding anything."))
        if sc.object_at(station) is not None:
            return self._record("place", args, self._reject("station_occupied", f"Station {station} is occupied."))
        return self._record("place", args, self.backend.place(hand, station))

    def move_object(self, hand: str, from_station: int, to_station: int) -> ActionResult:
        """pick + place + home, validated up front so nothing moves if the plan is impossible."""
        args = {"hand": hand, "from_station": from_station, "to_station": to_station}
        for st in (from_station, to_station):
            if err := self._check_hand(hand) or self._check_station(hand, st):
                return self._record("move_object", args, err)
        if err := self._check_reel_locked():
            return self._record("move_object", args, err)
        sc = self.backend.scene()
        if sc.hand(hand).holding:
            return self._record("move_object", args, self._reject("hand_busy", f"The {hand} hand already holds {sc.hand(hand).holding}."))
        if sc.object_at(from_station) is None:
            return self._record("move_object", args, self._reject("station_empty", f"Station {from_station} is empty."))
        if from_station != to_station and sc.object_at(to_station) is not None:
            return self._record("move_object", args, self._reject("station_occupied", f"Station {to_station} is occupied."))
        r = self.backend.pick(hand, from_station)
        if not r.ok:
            self.backend.home(hand)
            return self._record("move_object", args, ActionResult(False, r.code, r.message, self.scene()))
        r = self.backend.place(hand, to_station)
        if not r.ok:
            return self._record("move_object", args, r)
        self.backend.home(hand)
        return self._record("move_object", args, ActionResult(True, "ok", r.message, self.scene()))

    def rotate_reel(self, hand: str, steps: int) -> ActionResult:
        """Advance the reel `steps` positions (forward only) using `hand`.

        Rejected unless: the cell has a reel, the hand may operate it and holds nothing,
        and both hands are at home, because the tubes sweep through the arms' workspace."""
        args = {"hand": hand, "steps": steps}
        reel = self.wc.reel
        if reel is None:
            return self._record("rotate_reel", args, self._reject("no_reel", "This workcell has no reel."))
        if err := self._check_hand(hand):
            return self._record("rotate_reel", args, err)
        if hand not in reel.hands:
            return self._record("rotate_reel", args, self._reject(
                "unreachable", f"The {hand} hand cannot operate the reel; use one of {sorted(reel.hands)}."))
        if not 1 <= steps < reel.positions:
            return self._record("rotate_reel", args, self._reject(
                "invalid_argument", f"steps must be between 1 and {reel.positions - 1}; the ratchet only turns forward."))
        sc = self.backend.scene()
        if sc.hand(hand).holding:
            return self._record("rotate_reel", args, self._reject(
                "hand_busy", f"The {hand} hand holds {sc.hand(hand).holding}; place it first."))
        busy = [h.name for h in sc.hands if h.at_station is not None]
        if busy:
            return self._record("rotate_reel", args, self._reject(
                "arms_not_clear", f"Return {', '.join(busy)} hand(s) home before turning the reel."))
        return self._record("rotate_reel", args, self.backend.rotate_reel(hand, steps))

    def bring_tube(self, tube: int, hand: str | None = None) -> ActionResult:
        """Rotate forward until `tube` faces the arms. Picks a free reel hand if none is given."""
        args = {"tube": tube, "hand": hand}
        reel = self.wc.reel
        if reel is None:
            return self._record("bring_tube", args, self._reject("no_reel", "This workcell has no reel."))
        if not 1 <= tube <= reel.positions:
            return self._record("bring_tube", args, self._reject(
                "invalid_argument", f"tube must be between 1 and {reel.positions}."))
        sc = self.backend.scene()
        steps = reel.steps_to(sc.reel.tube_at_work, tube)
        if steps == 0:
            return self._record("bring_tube", args, ActionResult(
                True, "ok", f"Tube {tube} is already at the arms.", sc.to_dict()))
        if hand is None:
            free = [h.name for h in sc.hands if h.name in reel.hands and not h.holding]
            hand = free[0] if free else sorted(reel.hands)[0]
        return self.rotate_reel(hand, steps)

    def home(self, hand: str) -> ActionResult:
        if err := self._check_hand(hand):
            return self._record("home", {"hand": hand}, err)
        return self._record("home", {"hand": hand}, self.backend.home(hand))

    def stop(self) -> ActionResult:
        return self._record("stop", {}, self.backend.stop())

    def reset(self) -> ActionResult:
        return self._record("reset", {}, self.backend.reset())

    def recent_actions(self, n: int = 20) -> list[dict]:
        return list(self.log)[-n:]
