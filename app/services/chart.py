"""Services for natal chart calculation and snapshot persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import DomainValidationError, NotFoundError
from app.domain.ephemeris import (
    AnalyticalEphemerisProvider,
    EphemerisProvider,
    SwissEphemerisProvider,
    julian_day,
    normalize_degree,
)
from app.models.chart import Chart, ChartAngle, ChartAspect, ChartHouseCusp, ChartPosition
from app.models.astro_reference import Angle, Aspect, Body, House, Sign
from app.repositories.chart import ChartRepository
from app.repositories.astro_reference import AngleRepository, AspectRepository, BodyRepository
from app.schemas.chart import ChartFactorsRead, NatalChartCreate


RULER_FALLBACKS = {
    "ARIES": "MARS",
    "TAURUS": "VENUS",
    "GEMINI": "MERCURY",
    "CANCER": "MOON",
    "LEO": "SUN",
    "VIRGO": "MERCURY",
    "LIBRA": "VENUS",
    "SCORPIO": "MARS",
    "SAGITTARIUS": "JUPITER",
    "CAPRICORN": "SATURN",
    "AQUARIUS": "SATURN",
    "PISCES": "JUPITER",
}


def sign_code_from_degree(longitude_deg: float, signs: list[Sign]) -> str:
    normalized = normalize_degree(longitude_deg)
    for sign in signs:
        if sign.start_degree <= normalized < sign.end_degree:
            return sign.code
    return signs[-1].code


def house_number_from_degree(longitude_deg: float, asc_deg: float) -> int:
    normalized = normalize_degree(longitude_deg - asc_deg)
    return int(math.floor(normalized / 30.0)) + 1


def to_utc_datetime(payload: NatalChartCreate) -> datetime:
    local_dt = datetime.combine(payload.birth_date_local, payload.birth_time_local)
    offset = timedelta(minutes=payload.timezone_offset_minutes)
    local_tz = timezone(offset)
    return local_dt.replace(tzinfo=local_tz).astimezone(timezone.utc)


def calculate_sidereal_angles(
    dt_utc: datetime,
    latitude: float,
    longitude: float,
) -> dict[str, float]:
    jd = julian_day(dt_utc)
    t = (jd - 2451545.0) / 36525.0
    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * (t**2)
        - (t**3) / 38710000.0
    )
    lst = math.radians(normalize_degree(gmst + longitude))
    latitude_rad = math.radians(latitude)
    epsilon = math.radians(23.439291 - 0.0130042 * t)

    mc = normalize_degree(
        math.degrees(math.atan2(math.sin(lst), math.cos(lst) * math.cos(epsilon)))
    )
    asc = normalize_degree(
        math.degrees(
            math.atan2(
                -math.cos(lst),
                math.sin(epsilon) * math.tan(latitude_rad)
                + math.cos(epsilon) * math.sin(lst),
            )
        )
    )

    return {
        "ASC": asc,
        "MC": mc,
        "DSC": normalize_degree(asc + 180.0),
        "IC": normalize_degree(mc + 180.0),
    }


class NatalChartCalculationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chart_repo = ChartRepository(session)
        self.body_repo = BodyRepository(session)
        self.aspect_repo = AspectRepository(session)
        self.angle_repo = AngleRepository(session)
        self.settings = get_settings()
        self.ephemeris_provider = self._build_provider()

    def _build_provider(self) -> EphemerisProvider:
        provider_name = self.settings.ephemeris_provider.lower()
        if provider_name == "swisseph":
            return SwissEphemerisProvider(self.settings.swisseph_ephemeris_path)
        return AnalyticalEphemerisProvider()

    async def _load_reference_data(self) -> tuple[list[Body], list[Aspect], list[Angle], list[Sign], list[House]]:
        bodies = list(await self.body_repo.get_all(order_by=Body.code))
        aspects = list(await self.aspect_repo.get_all(order_by=Aspect.angle_degrees))
        angles = list(await self.angle_repo.get_all(order_by=Angle.code))
        signs_result = await self.session.execute(select(Sign).order_by(Sign.order_num))
        sign_models = list(signs_result.scalars().all())
        houses_result = await self.session.execute(select(House).order_by(House.number))
        house_models = list(houses_result.scalars().all())

        if not bodies or not aspects or not angles or not sign_models or not house_models:
            raise DomainValidationError(
                "Reference catalog is incomplete. Seed signs, bodies, houses, aspects and angles before chart calculation."
            )
        return bodies, aspects, angles, sign_models, house_models

    def _derive_rulerships(
        self,
        positions: list[ChartPosition],
        house_cusps: list[ChartHouseCusp],
        bodies: list[Body],
    ) -> dict[str, list[int]]:
        ruler_map: dict[str, str] = {}
        for body in bodies:
            if body.domicile_signs:
                for sign_code in body.domicile_signs:
                    ruler_map.setdefault(sign_code, body.code)

        for sign_code, body_code in RULER_FALLBACKS.items():
            ruler_map.setdefault(sign_code, body_code)

        ruled_houses_by_body: dict[str, list[int]] = {position.body_code: [] for position in positions}
        for cusp in house_cusps:
            ruler_body_code = ruler_map.get(cusp.sign_code)
            if ruler_body_code is not None and ruler_body_code in ruled_houses_by_body:
                ruled_houses_by_body[ruler_body_code].append(cusp.house_number)

        for position in positions:
            position.rulerships_json = ruled_houses_by_body.get(position.body_code) or []

        return ruled_houses_by_body

    def _build_house_cusps(
        self,
        asc_deg: float,
        signs: list[Sign],
    ) -> list[ChartHouseCusp]:
        cusps: list[ChartHouseCusp] = []
        for house_number in range(1, 13):
            longitude_deg = normalize_degree(asc_deg + (house_number - 1) * 30.0)
            cusps.append(
                ChartHouseCusp(
                    house_number=house_number,
                    longitude_deg=longitude_deg,
                    sign_code=sign_code_from_degree(longitude_deg, signs),
                )
            )
        return cusps

    def _build_angles(
        self,
        angle_degrees: dict[str, float],
        angle_refs: list[Angle],
        signs: list[Sign],
    ) -> list[ChartAngle]:
        angle_ids = {angle.code: angle.id for angle in angle_refs}
        return [
            ChartAngle(
                angle_id=angle_ids.get(code),
                angle_code=code,
                longitude_deg=longitude_deg,
                sign_code=sign_code_from_degree(longitude_deg, signs),
            )
            for code, longitude_deg in angle_degrees.items()
        ]

    def _build_aspects(
        self,
        positions: list[ChartPosition],
        aspect_refs: list[Aspect],
    ) -> list[ChartAspect]:
        chart_aspects: list[ChartAspect] = []
        aspect_ref_by_code = {aspect.code: aspect for aspect in aspect_refs}

        for index, first in enumerate(positions):
            for second in positions[index + 1:]:
                separation = abs(first.longitude_deg - second.longitude_deg) % 360.0
                if separation > 180.0:
                    separation = 360.0 - separation

                matched_aspect: Aspect | None = None
                matched_orb: float | None = None
                for aspect in aspect_refs:
                    orb = abs(separation - aspect.angle_degrees)
                    if orb <= aspect.max_orb_default:
                        if matched_orb is None or orb < matched_orb:
                            matched_aspect = aspect
                            matched_orb = orb

                if matched_aspect is None or matched_orb is None:
                    continue

                signed_delta = ((second.longitude_deg - first.longitude_deg) - matched_aspect.angle_degrees + 540.0) % 360.0 - 180.0
                relative_speed = (first.speed_deg_per_day or 0.0) - (second.speed_deg_per_day or 0.0)
                applying = signed_delta * relative_speed < 0

                chart_aspects.append(
                    ChartAspect(
                        aspect_id=aspect_ref_by_code[matched_aspect.code].id,
                        body_a_code=first.body_code,
                        body_b_code=second.body_code,
                        aspect_code=matched_aspect.code,
                        exact_angle_deg=matched_aspect.angle_degrees,
                        orb_deg=round(matched_orb, 4),
                        applying=applying,
                    )
                )

        return chart_aspects

    async def create_natal_chart(self, payload: NatalChartCreate) -> Chart:
        bodies, aspects, angles, signs, _houses = await self._load_reference_data()
        dt_utc = to_utc_datetime(payload)
        body_codes = [body.code for body in bodies]
        raw_positions = self.ephemeris_provider.calculate_body_positions(dt_utc, body_codes)

        angle_degrees = calculate_sidereal_angles(dt_utc, payload.latitude, payload.longitude)
        house_cusps = self._build_house_cusps(angle_degrees["ASC"], signs)

        body_refs = {body.code: body for body in bodies}
        positions = [
            ChartPosition(
                body_id=body_refs[position.body_code].id,
                body_code=position.body_code,
                longitude_deg=position.longitude_deg,
                latitude_deg=position.latitude_deg,
                speed_deg_per_day=position.speed_deg_per_day,
                is_retrograde=position.is_retrograde,
                sign_code=sign_code_from_degree(position.longitude_deg, signs),
                house_number=house_number_from_degree(position.longitude_deg, angle_degrees["ASC"]),
            )
            for position in raw_positions
        ]

        chart_angles = self._build_angles(angle_degrees, angles, signs)
        self._derive_rulerships(positions, house_cusps, bodies)
        chart_aspects = self._build_aspects(positions, aspects)

        chart = Chart(
            chart_type="natal",
            name=payload.name,
            provider=self.ephemeris_provider.provider_name,
            house_system=payload.house_system,
            birth_date_local=payload.birth_date_local,
            birth_time_local=payload.birth_time_local,
            birth_datetime_utc=dt_utc,
            timezone_offset_minutes=payload.timezone_offset_minutes,
            location_name=payload.location_name,
            latitude=payload.latitude,
            longitude=payload.longitude,
            notes=payload.notes,
            metadata_json=payload.metadata_json,
            positions=positions,
            aspects=chart_aspects,
            angles=chart_angles,
            house_cusps=house_cusps,
        )
        created = await self.chart_repo.create(chart)
        full_chart = await self.chart_repo.get_by_id_full(created.id)
        if full_chart is None:
            raise NotFoundError(f"Chart {created.id} not found after creation")
        return full_chart

    async def get_chart(self, chart_id: uuid.UUID) -> Chart:
        chart = await self.chart_repo.get_by_id_full(chart_id)
        if chart is None:
            raise NotFoundError(f"Chart {chart_id} not found")
        return chart

    async def list_chart_factors(self, chart_id: uuid.UUID) -> ChartFactorsRead:
        chart = await self.get_chart(chart_id)
        rulerships = {
            position.body_code: [int(house) for house in (position.rulerships_json or [])]
            for position in chart.positions
        }
        return ChartFactorsRead(
            chart_id=chart.id,
            provider=chart.provider,
            positions=chart.positions,
            aspects=chart.aspects,
            angles=chart.angles,
            house_cusps=chart.house_cusps,
            rulerships=rulerships,
        )
