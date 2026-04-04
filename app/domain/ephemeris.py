"""Ephemeris provider abstraction and built-in implementations.

The analytical provider is deterministic and lightweight, which keeps
tests and local development fast. A Swiss Ephemeris adapter is included
behind an optional import so the service layer is already prepared for a
precision provider without coupling the rest of the app to that package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Protocol


@dataclass(slots=True)
class EphemerisBodyPosition:
    body_code: str
    longitude_deg: float
    latitude_deg: float
    speed_deg_per_day: float
    is_retrograde: bool


class EphemerisProvider(Protocol):
    provider_name: str

    def calculate_body_positions(
        self,
        dt_utc: datetime,
        body_codes: list[str],
    ) -> list[EphemerisBodyPosition]:
        ...


ANALYTICAL_BASE_LONGITUDES = {
    "SUN": 280.466,
    "MOON": 218.316,
    "MERCURY": 252.251,
    "VENUS": 181.979,
    "MARS": 355.433,
    "JUPITER": 34.351,
    "SATURN": 50.077,
}

ANALYTICAL_ORBITAL_PERIODS = {
    "SUN": 365.256,
    "MOON": 27.32166,
    "MERCURY": 87.969,
    "VENUS": 224.701,
    "MARS": 686.98,
    "JUPITER": 4332.59,
    "SATURN": 10759.22,
}

SWISSEPH_BODY_CODES = {
    "SUN": 0,
    "MOON": 1,
    "MERCURY": 2,
    "VENUS": 3,
    "MARS": 4,
    "JUPITER": 5,
    "SATURN": 6,
}


def normalize_degree(value: float) -> float:
    return value % 360.0


def julian_day(dt_utc: datetime) -> float:
    dt_utc = dt_utc.astimezone(timezone.utc)
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day + (
        dt_utc.hour / 24
        + dt_utc.minute / 1440
        + dt_utc.second / 86400
        + dt_utc.microsecond / 86400_000000
    )

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


class AnalyticalEphemerisProvider:
    provider_name = "analytical"

    def calculate_body_positions(
        self,
        dt_utc: datetime,
        body_codes: list[str],
    ) -> list[EphemerisBodyPosition]:
        days_since_j2000 = julian_day(dt_utc) - 2451545.0
        positions: list[EphemerisBodyPosition] = []

        for body_code in body_codes:
            base_longitude = ANALYTICAL_BASE_LONGITUDES[body_code]
            orbital_period = ANALYTICAL_ORBITAL_PERIODS[body_code]
            speed = 360.0 / orbital_period
            longitude = normalize_degree(base_longitude + days_since_j2000 * speed)
            positions.append(
                EphemerisBodyPosition(
                    body_code=body_code,
                    longitude_deg=longitude,
                    latitude_deg=0.0,
                    speed_deg_per_day=speed,
                    is_retrograde=False,
                )
            )

        return positions


class SwissEphemerisProvider:
    provider_name = "swisseph"

    def __init__(self, ephemeris_path: str | None = None) -> None:
        try:
            import swisseph as swe
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "swisseph is not installed. Use the analytical provider or install pyswisseph."
            ) from exc

        self._swe = swe
        if ephemeris_path:
            self._swe.set_ephe_path(ephemeris_path)

    def calculate_body_positions(
        self,
        dt_utc: datetime,
        body_codes: list[str],
    ) -> list[EphemerisBodyPosition]:
        jd = julian_day(dt_utc)
        flags = self._swe.FLG_SWIEPH | self._swe.FLG_SPEED
        positions: list[EphemerisBodyPosition] = []

        for body_code in body_codes:
            body_id = SWISSEPH_BODY_CODES[body_code]
            result, _ = self._swe.calc_ut(jd, body_id, flags)
            positions.append(
                EphemerisBodyPosition(
                    body_code=body_code,
                    longitude_deg=normalize_degree(result[0]),
                    latitude_deg=float(result[1]),
                    speed_deg_per_day=float(result[3]),
                    is_retrograde=float(result[3]) < 0,
                )
            )

        return positions
