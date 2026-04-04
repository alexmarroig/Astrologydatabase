"""Natal chart API endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AstroPlatformError, DomainValidationError, NotFoundError
from app.db.base import get_db
from app.schemas.chart import ChartFactorsRead, ChartRead, NatalChartCreate
from app.schemas.prioritization import InterpretiveSnapshotRead
from app.services.chart import NatalChartCalculationService
from app.services.prioritization import InterpretivePrioritizationService

router = APIRouter(tags=["Charts"])


def _handle_domain_error(exc: AstroPlatformError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post(
    "/natal",
    response_model=ChartRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and persist a natal chart snapshot",
)
async def create_natal_chart(
    payload: NatalChartCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartRead:
    svc = NatalChartCalculationService(db)
    try:
        chart = await svc.create_natal_chart(payload)
    except (DomainValidationError, NotFoundError) as exc:
        _handle_domain_error(exc)
    return ChartRead.model_validate(chart)


@router.get(
    "/{chart_id}",
    response_model=ChartRead,
    summary="Fetch a previously calculated chart",
)
async def get_chart(
    chart_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartRead:
    svc = NatalChartCalculationService(db)
    try:
        chart = await svc.get_chart(chart_id)
    except NotFoundError as exc:
        _handle_domain_error(exc)
    return ChartRead.model_validate(chart)


@router.get(
    "/{chart_id}/factors",
    response_model=ChartFactorsRead,
    summary="List calculated chart factors",
)
async def list_chart_factors(
    chart_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartFactorsRead:
    svc = NatalChartCalculationService(db)
    try:
        return await svc.list_chart_factors(chart_id)
    except NotFoundError as exc:
        _handle_domain_error(exc)


@router.post(
    "/{chart_id}/interpretive-priority",
    response_model=InterpretiveSnapshotRead,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate and persist interpretive prioritization",
)
async def calculate_interpretive_priority(
    chart_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretiveSnapshotRead:
    svc = InterpretivePrioritizationService(db)
    try:
        return await svc.calculate_snapshot(chart_id)
    except (DomainValidationError, NotFoundError) as exc:
        _handle_domain_error(exc)


@router.get(
    "/{chart_id}/interpretive-priority",
    response_model=InterpretiveSnapshotRead,
    summary="Fetch the persisted interpretive prioritization snapshot",
)
async def get_interpretive_priority(
    chart_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretiveSnapshotRead:
    svc = InterpretivePrioritizationService(db)
    try:
        return await svc.get_snapshot(chart_id)
    except NotFoundError as exc:
        _handle_domain_error(exc)
