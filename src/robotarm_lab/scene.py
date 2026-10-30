"""Scene state exchanged with Claude. Mirrors docs/scene-schema.md."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Grip = Literal["open", "closed", "holding"]


@dataclass
class ObjectState:
    id: str
    cls: str
    station: int | None          # None while held by a hand
    held_by: str | None = None
    confidence: float = 1.0      # detector confidence; 1.0 in simulation


@dataclass
class HandState:
    name: str
    grip: Grip = "open"
    holding: str | None = None
    at_station: int | None = None  # None = at home pose


@dataclass
class Scene:
    timestamp: float
    estopped: bool
    objects: list[ObjectState] = field(default_factory=list)
    hands: list[HandState] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        for o in d["objects"]:
            o["class"] = o.pop("cls")
        return d

    def object_at(self, station: int) -> ObjectState | None:
        return next((o for o in self.objects if o.station == station), None)

    def hand(self, name: str) -> HandState:
        return next(h for h in self.hands if h.name == name)


@dataclass
class ActionResult:
    ok: bool
    code: str
    message: str
    scene: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)
