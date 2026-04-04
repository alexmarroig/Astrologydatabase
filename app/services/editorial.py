"""
Editorial service layer.

Contains business logic that sits between API routers and repositories:
  - Editorial workflow state machine (status transitions)
  - Uniqueness validation
  - Version increment on update
  - Cascade rules

Workflow valid transitions:
  draft → review → approved → published
  any → deprecated  (manual deprecation by approver)
  review → draft    (send back for revision)
  approved → review (send back for re-review)
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RuleStatus
from app.core.exceptions import (
    ConflictError,
    EditorialWorkflowError,
    NotFoundError,
)
from app.models.editorial import (
    InterpretationBlock,
    InterpretationRule,
    School,
    Source,
)
from app.repositories.editorial import (
    InterpretationBlockRepository,
    InterpretationRuleRepository,
    SchoolRepository,
    SourceRepository,
)
from app.schemas.editorial import (
    InterpretationBlockCreate,
    InterpretationBlockUpdate,
    InterpretationRuleCreate,
    InterpretationRuleUpdate,
    SchoolCreate,
    SchoolUpdate,
    SourceCreate,
    SourceUpdate,
)

# ── Valid workflow transitions ─────────────────────────────────────────────────
VALID_TRANSITIONS: dict[str, set[str]] = {
    RuleStatus.DRAFT.value: {RuleStatus.REVIEW.value, RuleStatus.DEPRECATED.value},
    RuleStatus.REVIEW.value: {
        RuleStatus.DRAFT.value,
        RuleStatus.APPROVED.value,
        RuleStatus.DEPRECATED.value,
    },
    RuleStatus.APPROVED.value: {
        RuleStatus.REVIEW.value,
        RuleStatus.PUBLISHED.value,
        RuleStatus.DEPRECATED.value,
    },
    RuleStatus.PUBLISHED.value: {RuleStatus.DEPRECATED.value},
    RuleStatus.DEPRECATED.value: set(),  # Terminal state
}


# ── School Service ─────────────────────────────────────────────────────────────

class SchoolService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SchoolRepository(session)

    async def list_schools(self, active_only: bool = True) -> list[School]:
        if active_only:
            return await self.repo.get_active()
        return list(await self.repo.get_all(order_by=School.code))

    async def get_school(self, id: uuid.UUID) -> School:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise NotFoundError(f"School {id} not found")
        return obj

    async def get_school_by_code(self, code: str) -> School:
        obj = await self.repo.get_by_code(code)
        if not obj:
            raise NotFoundError(f"School with code '{code}' not found")
        return obj

    async def create_school(self, data: SchoolCreate) -> School:
        if await self.repo.code_exists(data.code):
            raise ConflictError(f"School with code '{data.code}' already exists")
        obj = School(**data.model_dump())
        return await self.repo.create(obj)

    async def update_school(self, id: uuid.UUID, data: SchoolUpdate) -> School:
        obj = await self.get_school(id)
        update_data = data.model_dump(exclude_none=True)
        return await self.repo.update_fields(id, update_data)

    async def delete_school(self, id: uuid.UUID) -> None:
        deleted = await self.repo.delete(id)
        if not deleted:
            raise NotFoundError(f"School {id} not found")


# ── Source Service ─────────────────────────────────────────────────────────────

class SourceService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SourceRepository(session)

    async def list_sources(
        self, *, offset: int = 0, limit: int = 100, active_only: bool = True
    ) -> list[Source]:
        return await self.repo.get_all_with_school(
            offset=offset, limit=limit, active_only=active_only
        )

    async def get_source(self, id: uuid.UUID) -> Source:
        obj = await self.repo.get_by_id_with_school(id)
        if not obj:
            raise NotFoundError(f"Source {id} not found")
        return obj

    async def create_source(self, data: SourceCreate) -> Source:
        if data.isbn and await self.repo.isbn_exists(data.isbn):
            raise ConflictError(f"Source with ISBN '{data.isbn}' already exists")
        obj = Source(**data.model_dump())
        return await self.repo.create(obj)

    async def update_source(self, id: uuid.UUID, data: SourceUpdate) -> Source:
        await self.get_source(id)  # ensures it exists
        update_data = data.model_dump(exclude_none=True)
        if "isbn" in update_data:
            isbn = update_data["isbn"]
            if isbn and await self.repo.isbn_exists(isbn, exclude_id=id):
                raise ConflictError(f"Source with ISBN '{isbn}' already exists")
        return await self.repo.update_fields(id, update_data)

    async def delete_source(self, id: uuid.UUID) -> None:
        deleted = await self.repo.delete(id)
        if not deleted:
            raise NotFoundError(f"Source {id} not found")


# ── InterpretationRule Service ────────────────────────────────────────────────

class InterpretationRuleService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = InterpretationRuleRepository(session)

    async def list_rules(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        school_id: uuid.UUID | None = None,
        status: str | None = None,
        rule_type: str | None = None,
    ) -> list[InterpretationRule]:
        return await self.repo.get_all_paginated(
            offset=offset,
            limit=limit,
            school_id=school_id,
            status=status,
            rule_type=rule_type,
        )

    async def get_rule(self, id: uuid.UUID) -> InterpretationRule:
        obj = await self.repo.get_by_id_full(id)
        if not obj:
            raise NotFoundError(f"InterpretationRule {id} not found")
        return obj

    async def create_rule(self, data: InterpretationRuleCreate) -> InterpretationRule:
        exists = await self.repo.canonical_code_exists(
            data.canonical_code, data.school_id
        )
        if exists:
            raise ConflictError(
                f"Rule '{data.canonical_code}' already exists for this school"
            )
        obj = InterpretationRule(**data.model_dump(), status=RuleStatus.DRAFT.value, version=1)
        created = await self.repo.create(obj)
        full_obj = await self.repo.get_by_id_full(created.id)
        return full_obj or created

    async def update_rule(
        self, id: uuid.UUID, data: InterpretationRuleUpdate
    ) -> InterpretationRule:
        obj = await self.get_rule(id)
        update_data = data.model_dump(exclude_none=True)

        # Handle status transition validation
        if "status" in update_data:
            new_status = update_data["status"]
            current_status = obj.status
            allowed = VALID_TRANSITIONS.get(current_status, set())
            if new_status not in allowed:
                raise EditorialWorkflowError(
                    f"Cannot transition from '{current_status}' to '{new_status}'. "
                    f"Allowed: {allowed or 'none (terminal state)'}"
                )

        # Increment version on any content update
        content_fields = {
            "canonical_code", "rule_type", "subject_a_type", "subject_a_id",
            "subject_b_type", "subject_b_id", "subject_c_type", "subject_c_id",
            "notes", "interpretive_weight",
        }
        if update_data.keys() & content_fields:
            update_data["version"] = obj.version + 1

        # Validate canonical_code uniqueness if changing it
        if "canonical_code" in update_data:
            school_id = update_data.get("school_id", obj.school_id)
            exists = await self.repo.canonical_code_exists(
                update_data["canonical_code"], school_id, exclude_id=id
            )
            if exists:
                raise ConflictError(
                    f"Rule '{update_data['canonical_code']}' already exists for this school"
                )

        updated = await self.repo.update_fields(id, update_data)
        if updated is None:
            raise NotFoundError(f"InterpretationRule {id} not found")
        full_obj = await self.repo.get_by_id_full(id)
        return full_obj or updated

    async def transition_status(
        self, id: uuid.UUID, new_status: str
    ) -> InterpretationRule:
        """Dedicated method for status-only transitions."""
        update = InterpretationRuleUpdate(status=new_status)
        return await self.update_rule(id, update)

    async def delete_rule(self, id: uuid.UUID) -> None:
        """
        Hard delete. Only allowed for rules in 'draft' status.
        Published rules should be deprecated, not deleted.
        """
        obj = await self.get_rule(id)
        if obj.status == RuleStatus.PUBLISHED.value:
            raise EditorialWorkflowError(
                "Published rules cannot be deleted. Deprecate them instead."
            )
        deleted = await self.repo.delete(id)
        if not deleted:
            raise NotFoundError(f"InterpretationRule {id} not found")


# ── InterpretationBlock Service ───────────────────────────────────────────────

class InterpretationBlockService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = InterpretationBlockRepository(session)
        self.rule_repo = InterpretationRuleRepository(session)

    async def list_blocks_for_rule(
        self, rule_id: uuid.UUID
    ) -> list[InterpretationBlock]:
        # Verify rule exists
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise NotFoundError(f"InterpretationRule {rule_id} not found")
        return await self.repo.get_by_rule(rule_id)

    async def get_block(self, id: uuid.UUID) -> InterpretationBlock:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise NotFoundError(f"InterpretationBlock {id} not found")
        return obj

    async def create_block(
        self, data: InterpretationBlockCreate
    ) -> InterpretationBlock:
        # Verify rule exists
        rule = await self.rule_repo.get_by_id(data.rule_id)
        if not rule:
            raise NotFoundError(f"InterpretationRule {data.rule_id} not found")

        # Prevent duplicate theme per rule
        existing = await self.repo.get_by_rule_and_theme(data.rule_id, data.theme)
        if existing:
            raise ConflictError(
                f"Block with theme '{data.theme}' already exists for this rule. "
                "Update the existing block instead."
            )
        obj = InterpretationBlock(**data.model_dump())
        return await self.repo.create(obj)

    async def update_block(
        self, id: uuid.UUID, data: InterpretationBlockUpdate
    ) -> InterpretationBlock:
        await self.get_block(id)  # ensure exists
        update_data = data.model_dump(exclude_none=True)
        return await self.repo.update_fields(id, update_data)

    async def delete_block(self, id: uuid.UUID) -> None:
        deleted = await self.repo.delete(id)
        if not deleted:
            raise NotFoundError(f"InterpretationBlock {id} not found")
