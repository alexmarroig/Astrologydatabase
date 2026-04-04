"""Interpretive prioritization engine for natal chart factors."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import RuleStatus, RuleType
from app.core.exceptions import DomainValidationError, NotFoundError
from app.models.chart import Chart, ChartAspect, ChartPosition
from app.models.editorial import InterpretationRule, School
from app.models.prioritization import (
    InterpretiveMatch,
    InterpretivePriority,
    ThematicCluster,
)
from app.repositories.chart import ChartRepository
from app.repositories.editorial import InterpretationRuleRepository, SchoolRepository
from app.repositories.prioritization import (
    InterpretiveMatchRepository,
    InterpretivePriorityRepository,
    PrioritizationSnapshotRepository,
    ThematicClusterRepository,
)
from app.schemas.prioritization import (
    InterpretiveMatchRead,
    InterpretivePriorityRead,
    InterpretiveSnapshotRead,
    RuleSummaryRead,
    ThematicClusterRead,
)

ANGULAR_HOUSES = {1, 4, 7, 10}
SUCCEDENT_HOUSES = {2, 5, 8, 11}
SUPPORTED_RULE_TYPES = (
    RuleType.PLANET_IN_SIGN.value,
    RuleType.PLANET_IN_HOUSE.value,
    RuleType.ASPECT_PLANET_PLANET.value,
    RuleType.RULER_IN_HOUSE.value,
    RuleType.RULER_IN_SIGN.value,
)


@dataclass(slots=True)
class PriorityAggregate:
    rule: InterpretationRule
    primary_match: InterpretiveMatch
    matches: list[InterpretiveMatch]
    base_total: float
    redundancy_group: str
    matched_themes: list[str]
    repetition_score: float = 0.0
    total_score: float = 0.0
    rank: int = 0


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _house_strength(house_number: int | None) -> float:
    if house_number in ANGULAR_HOUSES:
        return 1.8
    if house_number in SUCCEDENT_HOUSES:
        return 0.9
    if house_number is not None:
        return 0.3
    return 0.0


class InterpretivePrioritizationService:
    """Builds and persists the intermediate interpretive selection layer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.chart_repo = ChartRepository(session)
        self.school_repo = SchoolRepository(session)
        self.rule_repo = InterpretationRuleRepository(session)
        self.match_repo = InterpretiveMatchRepository(session)
        self.priority_repo = InterpretivePriorityRepository(session)
        self.cluster_repo = ThematicClusterRepository(session)
        self.snapshot_repo = PrioritizationSnapshotRepository(session)

    async def calculate_snapshot(
        self,
        chart_id: uuid.UUID,
        *,
        school_code: str | None = None,
    ) -> InterpretiveSnapshotRead:
        chart = await self._get_chart(chart_id)
        school = await self._resolve_school(school_code)
        rules = await self.rule_repo.get_published_for_school(
            school.id,
            rule_types=SUPPORTED_RULE_TYPES,
        )

        matches = self._build_matches(chart, rules)
        await self.snapshot_repo.delete_for_chart(chart.id)

        self.session.add_all(matches)
        await self.session.flush()

        priorities = self._build_priorities(chart.id, matches)
        self.session.add_all(priorities)
        await self.session.flush()

        clusters = self._build_clusters(chart.id, priorities)
        self.session.add_all(clusters)
        await self.session.flush()

        return await self._serialize_snapshot(chart.id, school.code)

    async def get_snapshot(
        self,
        chart_id: uuid.UUID,
        *,
        school_code: str | None = None,
    ) -> InterpretiveSnapshotRead:
        await self._get_chart(chart_id)
        school = await self._resolve_school(school_code)
        priorities = await self.priority_repo.list_for_chart(chart_id)
        matches = await self.match_repo.list_for_chart(chart_id)
        clusters = await self.cluster_repo.list_for_chart(chart_id)
        if not priorities and not matches and not clusters:
            raise NotFoundError(
                f"Interpretive prioritization has not been calculated for chart {chart_id}"
            )
        return await self._serialize_snapshot(chart_id, school.code)

    async def _get_chart(self, chart_id: uuid.UUID) -> Chart:
        chart = await self.chart_repo.get_by_id_full(chart_id)
        if chart is None:
            raise NotFoundError(f"Chart {chart_id} not found")
        return chart

    async def _resolve_school(self, school_code: str | None) -> School:
        effective_code = school_code or self.settings.default_school
        school = await self.school_repo.get_by_code(effective_code)
        if school is None:
            raise NotFoundError(f"School with code '{effective_code}' not found")
        return school

    def _build_matches(
        self,
        chart: Chart,
        rules: list[InterpretationRule],
    ) -> list[InterpretiveMatch]:
        positions_by_body = {position.body_code: position for position in chart.positions}
        asc_ruler_bodies = {
            position.body_code
            for position in chart.positions
            if 1 in {int(house) for house in (position.rulerships_json or [])}
        }
        matches: list[InterpretiveMatch] = []

        for rule in rules:
            if rule.status != RuleStatus.PUBLISHED.value:
                continue

            if rule.rule_type == RuleType.PLANET_IN_SIGN.value:
                position = positions_by_body.get(rule.subject_a_id or "")
                if position is None or position.sign_code != rule.subject_b_id:
                    continue
                matches.append(
                    self._make_match(
                        chart_id=chart.id,
                        rule=rule,
                        factor_type=RuleType.PLANET_IN_SIGN.value,
                        factor_key=f"planet_in_sign:{position.body_code}:{position.sign_code}",
                        angularity_score=_house_strength(position.house_number),
                        exactness_score=0.0,
                        asc_ruler_score=2.0 if position.body_code in asc_ruler_bodies else 0.0,
                        details={
                            "body_code": position.body_code,
                            "sign_code": position.sign_code,
                            "house_number": position.house_number,
                        },
                    )
                )

            elif rule.rule_type == RuleType.PLANET_IN_HOUSE.value:
                position = positions_by_body.get(rule.subject_a_id or "")
                target_house = _safe_int(rule.subject_b_id)
                if position is None or position.house_number != target_house:
                    continue
                matches.append(
                    self._make_match(
                        chart_id=chart.id,
                        rule=rule,
                        factor_type=RuleType.PLANET_IN_HOUSE.value,
                        factor_key=f"planet_in_house:{position.body_code}:{position.house_number}",
                        angularity_score=_house_strength(position.house_number),
                        exactness_score=0.0,
                        asc_ruler_score=2.0 if position.body_code in asc_ruler_bodies else 0.0,
                        details={
                            "body_code": position.body_code,
                            "house_number": position.house_number,
                            "sign_code": position.sign_code,
                        },
                    )
                )

            elif rule.rule_type == RuleType.ASPECT_PLANET_PLANET.value:
                matches.extend(
                    self._match_aspect_rule(
                        chart_id=chart.id,
                        rule=rule,
                        chart_aspects=chart.aspects,
                        positions_by_body=positions_by_body,
                        asc_ruler_bodies=asc_ruler_bodies,
                    )
                )

            elif rule.rule_type == RuleType.RULER_IN_HOUSE.value:
                matches.extend(
                    self._match_regency_rule(
                        chart_id=chart.id,
                        rule=rule,
                        positions=chart.positions,
                        asc_ruler_bodies=asc_ruler_bodies,
                        target="house",
                    )
                )

            elif rule.rule_type == RuleType.RULER_IN_SIGN.value:
                matches.extend(
                    self._match_regency_rule(
                        chart_id=chart.id,
                        rule=rule,
                        positions=chart.positions,
                        asc_ruler_bodies=asc_ruler_bodies,
                        target="sign",
                    )
                )

        return matches

    def _make_match(
        self,
        *,
        chart_id: uuid.UUID,
        rule: InterpretationRule,
        factor_type: str,
        factor_key: str,
        angularity_score: float,
        exactness_score: float,
        asc_ruler_score: float,
        details: dict[str, Any],
    ) -> InterpretiveMatch:
        themes = _unique_ordered([block.theme for block in rule.blocks])
        base_weight = float(rule.interpretive_weight)
        raw_score = round(
            base_weight + angularity_score + exactness_score + asc_ruler_score,
            4,
        )
        return InterpretiveMatch(
            chart_id=chart_id,
            rule_id=rule.id,
            rule=rule,
            factor_type=factor_type,
            factor_key=factor_key,
            base_weight=base_weight,
            angularity_score=round(angularity_score, 4),
            exactness_score=round(exactness_score, 4),
            asc_ruler_score=round(asc_ruler_score, 4),
            raw_score=raw_score,
            theme_codes_json=themes,
            details_json=details,
        )

    def _match_aspect_rule(
        self,
        *,
        chart_id: uuid.UUID,
        rule: InterpretationRule,
        chart_aspects: list[ChartAspect],
        positions_by_body: dict[str, ChartPosition],
        asc_ruler_bodies: set[str],
    ) -> list[InterpretiveMatch]:
        expected_bodies = {rule.subject_a_id, rule.subject_b_id}
        matches: list[InterpretiveMatch] = []
        for aspect in chart_aspects:
            if {aspect.body_a_code, aspect.body_b_code} != expected_bodies:
                continue
            if aspect.aspect_code != rule.subject_c_id:
                continue

            position_a = positions_by_body.get(aspect.body_a_code)
            position_b = positions_by_body.get(aspect.body_b_code)
            angularity_score = max(
                _house_strength(position_a.house_number if position_a else None),
                _house_strength(position_b.house_number if position_b else None),
            )
            exactness_score = 2.5 / (1.0 + aspect.orb_deg)
            asc_ruler_score = 0.0
            if aspect.body_a_code in asc_ruler_bodies or aspect.body_b_code in asc_ruler_bodies:
                asc_ruler_score = 2.0

            matches.append(
                self._make_match(
                    chart_id=chart_id,
                    rule=rule,
                    factor_type=RuleType.ASPECT_PLANET_PLANET.value,
                    factor_key=(
                        f"aspect:{aspect.body_a_code}:{aspect.body_b_code}:{aspect.aspect_code}"
                    ),
                    angularity_score=angularity_score,
                    exactness_score=exactness_score,
                    asc_ruler_score=asc_ruler_score,
                    details={
                        "body_a_code": aspect.body_a_code,
                        "body_b_code": aspect.body_b_code,
                        "aspect_code": aspect.aspect_code,
                        "orb_deg": aspect.orb_deg,
                        "applying": aspect.applying,
                    },
                )
            )
        return matches

    def _match_regency_rule(
        self,
        *,
        chart_id: uuid.UUID,
        rule: InterpretationRule,
        positions: list[ChartPosition],
        asc_ruler_bodies: set[str],
        target: str,
    ) -> list[InterpretiveMatch]:
        expected_ruled_house = _safe_int(rule.subject_a_id)
        expected_body = rule.subject_b_id
        expected_target = rule.subject_c_id
        matches: list[InterpretiveMatch] = []

        for position in positions:
            ruled_houses = [int(house) for house in (position.rulerships_json or [])]
            if expected_body and position.body_code != expected_body:
                continue

            for ruled_house in ruled_houses:
                if expected_ruled_house is not None and ruled_house != expected_ruled_house:
                    continue
                if target == "house":
                    if expected_target is not None and position.house_number != _safe_int(expected_target):
                        continue
                    factor_key = (
                        f"ruler_in_house:{ruled_house}:{position.body_code}:{position.house_number}"
                    )
                    details = {
                        "ruled_house": ruled_house,
                        "ruler_body_code": position.body_code,
                        "house_number": position.house_number,
                        "sign_code": position.sign_code,
                    }
                else:
                    if expected_target is not None and position.sign_code != expected_target:
                        continue
                    factor_key = (
                        f"ruler_in_sign:{ruled_house}:{position.body_code}:{position.sign_code}"
                    )
                    details = {
                        "ruled_house": ruled_house,
                        "ruler_body_code": position.body_code,
                        "house_number": position.house_number,
                        "sign_code": position.sign_code,
                    }

                asc_ruler_score = 2.0 if ruled_house == 1 or position.body_code in asc_ruler_bodies else 0.0
                matches.append(
                    self._make_match(
                        chart_id=chart_id,
                        rule=rule,
                        factor_type=rule.rule_type,
                        factor_key=factor_key,
                        angularity_score=_house_strength(position.house_number),
                        exactness_score=0.0,
                        asc_ruler_score=asc_ruler_score,
                        details=details,
                    )
                )

        return matches

    def _build_priorities(
        self,
        chart_id: uuid.UUID,
        matches: list[InterpretiveMatch],
    ) -> list[InterpretivePriority]:
        aggregates_by_group: dict[str, list[PriorityAggregate]] = defaultdict(list)

        for match in matches:
            rule = match.rule
            themes = [str(theme) for theme in (match.theme_codes_json or [])]
            redundancy_group = self._redundancy_group_for_rule(rule, themes)
            aggregate = PriorityAggregate(
                rule=rule,
                primary_match=match,
                matches=[match],
                base_total=match.raw_score,
                redundancy_group=redundancy_group,
                matched_themes=themes,
            )
            aggregates_by_group[redundancy_group].append(aggregate)

        selected: list[PriorityAggregate] = []
        for redundancy_group, aggregates in aggregates_by_group.items():
            collapsed = max(
                aggregates,
                key=lambda item: (
                    item.base_total,
                    len(item.matched_themes),
                    item.rule.canonical_code,
                ),
            )
            collapsed.redundancy_group = redundancy_group
            selected.append(collapsed)

        theme_counter: Counter[str] = Counter()
        for aggregate in selected:
            theme_counter.update(set(aggregate.matched_themes))

        selected.sort(
            key=lambda item: (
                item.base_total,
                len(item.matched_themes),
                item.rule.canonical_code,
            ),
            reverse=True,
        )

        priorities: list[InterpretivePriority] = []
        for index, aggregate in enumerate(selected, start=1):
            repetition_score = round(
                sum(
                    max(0, theme_counter[theme] - 1) * 0.8
                    for theme in set(aggregate.matched_themes)
                ),
                4,
            )
            aggregate.repetition_score = repetition_score
            aggregate.total_score = round(aggregate.base_total + repetition_score, 4)

        selected.sort(
            key=lambda item: (
                item.total_score,
                item.base_total,
                len(item.matched_themes),
                item.rule.canonical_code,
            ),
            reverse=True,
        )

        for index, aggregate in enumerate(selected, start=1):
            aggregate.rank = index
            priorities.append(
                InterpretivePriority(
                    chart_id=chart_id,
                    rule_id=aggregate.rule.id,
                    rule=aggregate.rule,
                    primary_match_id=aggregate.primary_match.id,
                    primary_match=aggregate.primary_match,
                    rank=index,
                    total_score=aggregate.total_score,
                    redundancy_group=aggregate.redundancy_group,
                    thematic_repetition_score=aggregate.repetition_score,
                    match_count=len(aggregate.matches),
                    matched_themes_json=aggregate.matched_themes,
                    summary_json={
                        "canonical_code": aggregate.rule.canonical_code,
                        "factor_type": aggregate.primary_match.factor_type,
                        "factor_key": aggregate.primary_match.factor_key,
                        "raw_score": aggregate.primary_match.raw_score,
                    },
                )
            )

        return priorities

    def _build_clusters(
        self,
        chart_id: uuid.UUID,
        priorities: list[InterpretivePriority],
    ) -> list[ThematicCluster]:
        grouped: dict[str, list[InterpretivePriority]] = defaultdict(list)
        for priority in priorities:
            for theme_code in priority.matched_themes_json or []:
                grouped[str(theme_code)].append(priority)

        clusters: list[ThematicCluster] = []
        for theme_code, themed_priorities in grouped.items():
            sorted_priorities = sorted(
                themed_priorities,
                key=lambda item: (item.total_score, -item.rank),
                reverse=True,
            )
            clusters.append(
                ThematicCluster(
                    chart_id=chart_id,
                    theme_code=theme_code,
                    cluster_score=round(
                        sum(item.total_score for item in themed_priorities),
                        4,
                    ),
                    priority_count=len(themed_priorities),
                    top_priority_ids_json=[str(item.id) for item in sorted_priorities[:3]],
                    summary=(
                        f"{theme_code} reinforced by "
                        f"{', '.join(item.rule.canonical_code for item in sorted_priorities[:3])}"
                    ),
                    metadata_json={
                        "top_rule_codes": [
                            item.rule.canonical_code for item in sorted_priorities[:3]
                        ],
                    },
                )
            )

        clusters.sort(key=lambda item: (item.cluster_score, item.theme_code), reverse=True)
        return clusters

    def _redundancy_group_for_rule(
        self,
        rule: InterpretationRule,
        themes: list[str],
    ) -> str:
        if rule.metadata_json and isinstance(rule.metadata_json, dict):
            explicit_group = rule.metadata_json.get("redundancy_group")
            if explicit_group:
                return str(explicit_group)
        primary_theme = themes[0] if themes else "unclassified"
        return f"{rule.rule_type}:{rule.subject_a_id}:{rule.subject_b_id}:{rule.subject_c_id}:{primary_theme}"

    async def _serialize_snapshot(
        self,
        chart_id: uuid.UUID,
        school_code: str,
    ) -> InterpretiveSnapshotRead:
        matches = await self.match_repo.list_for_chart(chart_id)
        priorities = await self.priority_repo.list_for_chart(chart_id)
        clusters = await self.cluster_repo.list_for_chart(chart_id)
        timestamps = [item.updated_at for item in [*matches, *priorities, *clusters]]
        generated_at = max(timestamps) if timestamps else datetime.now(timezone.utc)
        return InterpretiveSnapshotRead(
            chart_id=chart_id,
            school_code=school_code,
            generated_at=generated_at,
            matches=[self._serialize_match(item) for item in matches],
            priorities=[self._serialize_priority(item) for item in priorities],
            clusters=[self._serialize_cluster(item) for item in clusters],
        )

    def _rule_summary(self, rule: InterpretationRule) -> RuleSummaryRead:
        return RuleSummaryRead(
            id=rule.id,
            canonical_code=rule.canonical_code,
            rule_type=rule.rule_type,
            subject_a_type=rule.subject_a_type,
            subject_a_id=rule.subject_a_id,
            subject_b_type=rule.subject_b_type,
            subject_b_id=rule.subject_b_id,
            subject_c_type=rule.subject_c_type,
            subject_c_id=rule.subject_c_id,
        )

    def _serialize_match(self, match: InterpretiveMatch) -> InterpretiveMatchRead:
        return InterpretiveMatchRead(
            id=match.id,
            created_at=match.created_at,
            updated_at=match.updated_at,
            chart_id=match.chart_id,
            rule_id=match.rule_id,
            factor_type=match.factor_type,
            factor_key=match.factor_key,
            base_weight=match.base_weight,
            angularity_score=match.angularity_score,
            exactness_score=match.exactness_score,
            asc_ruler_score=match.asc_ruler_score,
            raw_score=match.raw_score,
            theme_codes_json=[str(theme) for theme in (match.theme_codes_json or [])],
            details_json=match.details_json,
            rule=self._rule_summary(match.rule),
        )

    def _serialize_priority(
        self,
        priority: InterpretivePriority,
    ) -> InterpretivePriorityRead:
        return InterpretivePriorityRead(
            id=priority.id,
            created_at=priority.created_at,
            updated_at=priority.updated_at,
            chart_id=priority.chart_id,
            rule_id=priority.rule_id,
            primary_match_id=priority.primary_match_id,
            rank=priority.rank,
            total_score=priority.total_score,
            redundancy_group=priority.redundancy_group,
            thematic_repetition_score=priority.thematic_repetition_score,
            match_count=priority.match_count,
            matched_themes_json=[
                str(theme) for theme in (priority.matched_themes_json or [])
            ],
            summary_json=priority.summary_json,
            rule=self._rule_summary(priority.rule),
        )

    def _serialize_cluster(self, cluster: ThematicCluster) -> ThematicClusterRead:
        return ThematicClusterRead(
            id=cluster.id,
            created_at=cluster.created_at,
            updated_at=cluster.updated_at,
            chart_id=cluster.chart_id,
            theme_code=cluster.theme_code,
            cluster_score=cluster.cluster_score,
            priority_count=cluster.priority_count,
            top_priority_ids_json=list(cluster.top_priority_ids_json or []),
            summary=cluster.summary,
            metadata_json=cluster.metadata_json,
        )
