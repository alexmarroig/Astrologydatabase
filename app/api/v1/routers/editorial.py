"""
Editorial API endpoints.

Full CRUD for the editorial domain:
  - Schools
  - Sources
  - Interpretation Rules (with status workflow)
  - Interpretation Blocks
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RuleStatus, RuleType
from app.core.exceptions import (
    AstroPlatformError,
    ConflictError,
    EditorialWorkflowError,
    NotFoundError,
)
from app.db.base import get_db
from app.services.editorial import (
    InterpretationBlockService,
    InterpretationRuleService,
    SchoolService,
    SourceService,
)
from app.schemas.editorial import (
    InterpretationBlockCreate,
    InterpretationBlockList,
    InterpretationBlockRead,
    InterpretationBlockUpdate,
    InterpretationRuleCreate,
    InterpretationRuleList,
    InterpretationRuleRead,
    InterpretationRuleUpdate,
    SchoolCreate,
    SchoolList,
    SchoolRead,
    SchoolUpdate,
    SourceCreate,
    SourceList,
    SourceRead,
    SourceUpdate,
)

router = APIRouter(tags=["Editorial"])


def _handle_domain_error(exc: AstroPlatformError) -> None:
    """Convert domain exceptions to HTTP exceptions."""
    raise HTTPException(status_code=exc.status_code, detail=exc.detail)


# ── Schools ───────────────────────────────────────────────────────────────────

@router.get(
    "/schools",
    response_model=list[SchoolList],
    summary="List astrological schools",
)
async def list_schools(
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(True, description="Filter to active schools only"),
) -> list[SchoolList]:
    svc = SchoolService(db)
    schools = await svc.list_schools(active_only=active_only)
    return [SchoolList.model_validate(s) for s in schools]


@router.get(
    "/schools/{school_id}",
    response_model=SchoolRead,
    summary="Get school by ID",
)
async def get_school(
    school_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SchoolRead:
    svc = SchoolService(db)
    try:
        school = await svc.get_school(school_id)
    except NotFoundError as e:
        _handle_domain_error(e)
    return SchoolRead.model_validate(school)


@router.post(
    "/schools",
    response_model=SchoolRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new school",
)
async def create_school(
    payload: SchoolCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SchoolRead:
    svc = SchoolService(db)
    try:
        school = await svc.create_school(payload)
    except ConflictError as e:
        _handle_domain_error(e)
    return SchoolRead.model_validate(school)


@router.patch(
    "/schools/{school_id}",
    response_model=SchoolRead,
    summary="Update a school",
)
async def update_school(
    school_id: Annotated[uuid.UUID, Path()],
    payload: SchoolUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SchoolRead:
    svc = SchoolService(db)
    try:
        school = await svc.update_school(school_id, payload)
    except NotFoundError as e:
        _handle_domain_error(e)
    return SchoolRead.model_validate(school)


@router.delete(
    "/schools/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="Delete a school",
)
async def delete_school(
    school_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = SchoolService(db)
    try:
        await svc.delete_school(school_id)
    except NotFoundError as e:
        _handle_domain_error(e)


# ── Sources ───────────────────────────────────────────────────────────────────

@router.get(
    "/sources",
    response_model=list[SourceList],
    summary="List reference sources",
)
async def list_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(True),
) -> list[SourceList]:
    svc = SourceService(db)
    sources = await svc.list_sources(offset=offset, limit=limit, active_only=active_only)
    return [SourceList.model_validate(s) for s in sources]


@router.get(
    "/sources/{source_id}",
    response_model=SourceRead,
    summary="Get source by ID (with school detail)",
)
async def get_source(
    source_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceRead:
    svc = SourceService(db)
    try:
        source = await svc.get_source(source_id)
    except NotFoundError as e:
        _handle_domain_error(e)
    return SourceRead.model_validate(source)


@router.post(
    "/sources",
    response_model=SourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new reference source",
)
async def create_source(
    payload: SourceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceRead:
    svc = SourceService(db)
    try:
        source = await svc.create_source(payload)
    except ConflictError as e:
        _handle_domain_error(e)
    return SourceRead.model_validate(source)


@router.patch(
    "/sources/{source_id}",
    response_model=SourceRead,
    summary="Update a source",
)
async def update_source(
    source_id: Annotated[uuid.UUID, Path()],
    payload: SourceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceRead:
    svc = SourceService(db)
    try:
        source = await svc.update_source(source_id, payload)
    except (NotFoundError, ConflictError) as e:
        _handle_domain_error(e)
    return SourceRead.model_validate(source)


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="Delete a source",
)
async def delete_source(
    source_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = SourceService(db)
    try:
        await svc.delete_source(source_id)
    except NotFoundError as e:
        _handle_domain_error(e)


# ── Interpretation Rules ──────────────────────────────────────────────────────

@router.get(
    "/rules",
    response_model=list[InterpretationRuleList],
    summary="List interpretation rules",
    description=(
        "Filterable by school, status, and rule_type. "
        "Returns slim list schema — use GET /rules/{id} for full detail."
    ),
)
async def list_rules(
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    school_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, description="Filter by status: draft, review, approved, published, deprecated"),
    rule_type: str | None = Query(None, description="Filter by rule_type, e.g. planet_in_sign"),
) -> list[InterpretationRuleList]:
    svc = InterpretationRuleService(db)
    rules = await svc.list_rules(
        offset=offset,
        limit=limit,
        school_id=school_id,
        status=status,
        rule_type=rule_type,
    )
    return [InterpretationRuleList.model_validate(r) for r in rules]


@router.get(
    "/rules/{rule_id}",
    response_model=InterpretationRuleRead,
    summary="Get rule by ID (full detail with blocks)",
)
async def get_rule(
    rule_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretationRuleRead:
    svc = InterpretationRuleService(db)
    try:
        rule = await svc.get_rule(rule_id)
    except NotFoundError as e:
        _handle_domain_error(e)
    return InterpretationRuleRead.model_validate(rule)


@router.post(
    "/rules",
    response_model=InterpretationRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new interpretation rule",
    description=(
        "Creates a rule in 'draft' status. "
        "Use PATCH /rules/{id} with status field to advance through workflow."
    ),
)
async def create_rule(
    payload: InterpretationRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretationRuleRead:
    svc = InterpretationRuleService(db)
    try:
        rule = await svc.create_rule(payload)
    except (ConflictError, NotFoundError) as e:
        _handle_domain_error(e)
    return InterpretationRuleRead.model_validate(rule)


@router.patch(
    "/rules/{rule_id}",
    response_model=InterpretationRuleRead,
    summary="Update a rule (content or status)",
    description=(
        "All fields optional (PATCH). "
        "Status transitions are validated: draft→review→approved→published. "
        "Content updates increment the version counter."
    ),
)
async def update_rule(
    rule_id: Annotated[uuid.UUID, Path()],
    payload: InterpretationRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretationRuleRead:
    svc = InterpretationRuleService(db)
    try:
        rule = await svc.update_rule(rule_id, payload)
    except (NotFoundError, ConflictError, EditorialWorkflowError) as e:
        _handle_domain_error(e)
    return InterpretationRuleRead.model_validate(rule)


@router.post(
    "/rules/{rule_id}/transition",
    response_model=InterpretationRuleRead,
    summary="Transition rule status",
    description=(
        "Dedicated endpoint for editorial workflow transitions. "
        "Valid paths: draft→review, review→approved, approved→published, any→deprecated."
    ),
)
async def transition_rule_status(
    rule_id: Annotated[uuid.UUID, Path()],
    new_status: str = Query(..., description="Target status"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> InterpretationRuleRead:
    svc = InterpretationRuleService(db)
    try:
        rule = await svc.transition_status(rule_id, new_status)
    except (NotFoundError, EditorialWorkflowError) as e:
        _handle_domain_error(e)
    return InterpretationRuleRead.model_validate(rule)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="Delete a rule (only draft rules)",
    description="Published rules cannot be deleted. Deprecate them via status transition.",
)
async def delete_rule(
    rule_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = InterpretationRuleService(db)
    try:
        await svc.delete_rule(rule_id)
    except (NotFoundError, EditorialWorkflowError) as e:
        _handle_domain_error(e)


# ── Interpretation Blocks ─────────────────────────────────────────────────────

@router.get(
    "/rules/{rule_id}/blocks",
    response_model=list[InterpretationBlockRead],
    summary="List all blocks for a rule",
)
async def list_blocks_for_rule(
    rule_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InterpretationBlockRead]:
    svc = InterpretationBlockService(db)
    try:
        blocks = await svc.list_blocks_for_rule(rule_id)
    except NotFoundError as e:
        _handle_domain_error(e)
    return [InterpretationBlockRead.model_validate(b) for b in blocks]


@router.post(
    "/blocks",
    response_model=InterpretationBlockRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an interpretation block",
    description="Each theme can have at most one block per rule.",
)
async def create_block(
    payload: InterpretationBlockCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretationBlockRead:
    svc = InterpretationBlockService(db)
    try:
        block = await svc.create_block(payload)
    except (NotFoundError, ConflictError) as e:
        _handle_domain_error(e)
    return InterpretationBlockRead.model_validate(block)


@router.get(
    "/blocks/{block_id}",
    response_model=InterpretationBlockRead,
    summary="Get block by ID",
)
async def get_block(
    block_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretationBlockRead:
    svc = InterpretationBlockService(db)
    try:
        block = await svc.get_block(block_id)
    except NotFoundError as e:
        _handle_domain_error(e)
    return InterpretationBlockRead.model_validate(block)


@router.patch(
    "/blocks/{block_id}",
    response_model=InterpretationBlockRead,
    summary="Update an interpretation block",
)
async def update_block(
    block_id: Annotated[uuid.UUID, Path()],
    payload: InterpretationBlockUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterpretationBlockRead:
    svc = InterpretationBlockService(db)
    try:
        block = await svc.update_block(block_id, payload)
    except NotFoundError as e:
        _handle_domain_error(e)
    return InterpretationBlockRead.model_validate(block)


@router.delete(
    "/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="Delete an interpretation block",
)
async def delete_block(
    block_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = InterpretationBlockService(db)
    try:
        await svc.delete_block(block_id)
    except NotFoundError as e:
        _handle_domain_error(e)
