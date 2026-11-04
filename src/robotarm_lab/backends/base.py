"""Interface every arm backend implements (simulation, LeRobot SO-101, custom arms).

Backends execute ONE primitive and report what physically happened. They never decide
what to do next; that is the controller's (and Claude's) job. Safety limits live in the
firmware below the backend, not here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..scene import ActionResult, Scene


class Backend(ABC):
    @abstractmethod
    def scene(self) -> Scene:
        """Current state: objects per station, what each hand holds, e-stop flag."""

    @abstractmethod
    def pick(self, hand: str, station: int) -> ActionResult:
        """Grasp the object in `station` with `hand`. Codes: ok, grip_failed, station_empty."""

    @abstractmethod
    def place(self, hand: str, station: int) -> ActionResult:
        """Release the held object into `station`. Codes: ok, station_occupied, hand_empty."""

    @abstractmethod
    def home(self, hand: str) -> ActionResult:
        """Return `hand` to its home pose without releasing anything."""

    @abstractmethod
    def stop(self) -> ActionResult:
        """Software stop: halt all motion and latch until reset(). Hardware e-stop is separate."""

    @abstractmethod
    def reset(self) -> ActionResult:
        """Clear a software stop. Fails while the hardware e-stop is pressed."""

    def rotate_reel(self, hand: str, steps: int) -> ActionResult:
        """Advance the reel `steps` positions with `hand`: lift the latch, push a hub peg,
        release, and confirm the latch seated again at every step.
        Codes: ok, latch_failed (rotation stops at the last position where the latch seated)."""
        raise NotImplementedError("this backend has no reel")

    def capture(self) -> bytes | None:
        """JPEG of the workcell camera, or None if this backend has no camera."""
        return None
