"""Static description of the workcell: stations, hands and what each hand can reach."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

HANDS = ("left", "right")


@dataclass(frozen=True)
class Station:
    id: int
    label: str
    position_mm: tuple[float, float, float]


@dataclass(frozen=True)
class Hand:
    name: str
    home_mm: tuple[float, float, float]
    reach: frozenset[int]


@dataclass(frozen=True)
class InitialObject:
    id: str
    cls: str
    station: int


@dataclass
class Workcell:
    name: str
    stations: dict[int, Station]
    hands: dict[str, Hand]
    initial_objects: list[InitialObject] = field(default_factory=list)

    def can_reach(self, hand: str, station: int) -> bool:
        return hand in self.hands and station in self.hands[hand].reach

    @classmethod
    def load(cls, path: str | Path) -> "Workcell":
        data = tomllib.loads(Path(path).read_text())
        stations = {}
        for s in data.get("stations", []):
            st = Station(int(s["id"]), s.get("label", ""), tuple(s["position_mm"]))
            if st.id in stations:
                raise ValueError(f"duplicate station id {st.id}")
            stations[st.id] = st
        hands = {}
        for name, h in data.get("hands", {}).items():
            if name not in HANDS:
                raise ValueError(f"unknown hand '{name}', expected one of {HANDS}")
            reach = frozenset(int(x) for x in h.get("reach", []))
            missing = reach - stations.keys()
            if missing:
                raise ValueError(f"hand '{name}' reaches undefined stations {sorted(missing)}")
            hands[name] = Hand(name, tuple(h["home_mm"]), reach)
        objects = []
        used = set()
        for o in data.get("objects", []):
            obj = InitialObject(o["id"], o["class"], int(o["station"]))
            if obj.station not in stations:
                raise ValueError(f"object {obj.id} placed in undefined station {obj.station}")
            if obj.station in used:
                raise ValueError(f"station {obj.station} holds more than one object")
            used.add(obj.station)
            objects.append(obj)
        return cls(data.get("workcell", {}).get("name", "workcell"), stations, hands, objects)
