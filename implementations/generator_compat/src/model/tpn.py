"""Compatibility data layer reconstructed from the actual rmt_fms_generator call surface.

This is NOT the original lost package. It provides only the construction
dataclasses used by the generator; it does not implement original solver or
enabling methods. Every generated model is therefore a new reconstruction and
must be validated against the 36 historical L/H/place/transition counts before
use.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

INF = float('inf')


@dataclass(frozen=True)
class Interval:
    earliest: Fraction
    latest: Fraction


@dataclass(frozen=True)
class AuthorizedRange:
    l_min: Fraction
    l_max: Fraction
    u_min: Fraction
    u_max: Fraction
    resolution: Fraction


@dataclass(frozen=True)
class Place:
    name: str


@dataclass(frozen=True)
class Arc:
    from_node: str
    to_node: str


@dataclass
class Transition:
    name: str
    label: str
    is_fault: bool
    is_adjustable: bool
    interval: Interval
    admissible_intervals: Tuple[Interval, ...] = ()
    authorized_range: Optional[AuthorizedRange] = None


@dataclass
class TPN:
    places: Dict[str, Place]
    transitions: Dict[str, Transition]
    arcs: List[Arc]
    initial_marking: Dict[str, int]
    completion_markings: List[Dict[str, int]]
