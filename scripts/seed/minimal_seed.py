from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: F401 - ensure metadata/model registration
from app.core.config import get_settings
from app.domain.bootstrap_data import (
    ANGLES,
    ASPECTS,
    BODIES,
    HOUSES,
    SCHOOLS,
    SIGNS,
    SIGN_OPPOSITES,
)
from app.models.astro_reference import Angle, Aspect, Body, House, Sign
from app.models.editorial import School


def _upsert_by_field(session: Session, model, field_name: str, payload: dict):
    field = getattr(model, field_name)
    instance = session.scalar(select(model).where(field == payload[field_name]))
    if instance is None:
        instance = model(**payload)
        session.add(instance)
        session.flush()
        return instance

    for key, value in payload.items():
        setattr(instance, key, value)
    session.flush()
    return instance


def seed_minimal_data(session: Session) -> None:
    signs_by_code: dict[str, Sign] = {}
    for payload in SIGNS:
        sign = _upsert_by_field(session, Sign, "code", payload)
        signs_by_code[sign.code] = sign

    for code, opposite_code in SIGN_OPPOSITES.items():
        signs_by_code[code].opposite_sign_id = signs_by_code[opposite_code].id
    session.flush()

    for payload in BODIES:
        _upsert_by_field(session, Body, "code", payload)

    for payload in HOUSES:
        _upsert_by_field(session, House, "number", payload)

    for payload in ASPECTS:
        _upsert_by_field(session, Aspect, "code", payload)

    for payload in ANGLES:
        _upsert_by_field(session, Angle, "code", payload)

    for payload in SCHOOLS:
        _upsert_by_field(session, School, "code", payload)

    session.commit()


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)

    with Session(engine) as session:
        seed_minimal_data(session)

    print("Minimal seed completed.")


if __name__ == "__main__":
    main()
