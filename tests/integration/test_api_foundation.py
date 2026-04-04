from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_reference_and_school_lists_return_seeded_data(client, seeded_catalog):
    endpoints = [
        "/api/v1/reference/signs",
        "/api/v1/reference/bodies",
        "/api/v1/reference/houses",
        "/api/v1/reference/aspects",
        "/api/v1/editorial/schools",
    ]

    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert response.status_code == 200
        assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_sources_rules_and_blocks_crud_flow(client, seeded_catalog):
    school_id = str(seeded_catalog["default_school"].id)

    source_payload = {
        "title": "Astrologia Basica",
        "author": "Equipe Astro",
        "publication_year": 2024,
        "language": "pt",
        "school_id": school_id,
        "trust_level": "primary",
        "source_type": "book",
        "notes": "Fonte inicial para os testes.",
        "metadata": {"edition": "1"},
    }
    source_response = await client.post("/api/v1/editorial/sources", json=source_payload)
    assert source_response.status_code == 201
    source_data = source_response.json()

    listed_sources = await client.get("/api/v1/editorial/sources")
    assert listed_sources.status_code == 200
    assert any(item["id"] == source_data["id"] for item in listed_sources.json())

    updated_source = await client.patch(
        f"/api/v1/editorial/sources/{source_data['id']}",
        json={"notes": "Fonte revisada."},
    )
    assert updated_source.status_code == 200
    assert updated_source.json()["notes"] == "Fonte revisada."

    rule_payload = {
        "canonical_code": "SUN__PLANET_IN_SIGN__ARIES",
        "rule_type": "planet_in_sign",
        "subject_a_type": "body",
        "subject_a_id": "SUN",
        "subject_b_type": "sign",
        "subject_b_id": "ARIES",
        "school_id": school_id,
        "source_id": source_data["id"],
        "interpretive_weight": 7.5,
        "notes": "Regra inicial.",
        "metadata": {"seed": True},
    }
    rule_response = await client.post("/api/v1/editorial/rules", json=rule_payload)
    assert rule_response.status_code == 201
    rule_data = rule_response.json()
    assert rule_data["status"] == "draft"
    assert rule_data["version"] == 1

    listed_rules = await client.get("/api/v1/editorial/rules")
    assert listed_rules.status_code == 200
    assert any(item["id"] == rule_data["id"] for item in listed_rules.json())

    updated_rule = await client.patch(
        f"/api/v1/editorial/rules/{rule_data['id']}",
        json={"notes": "Regra revisada.", "interpretive_weight": 8.1},
    )
    assert updated_rule.status_code == 200
    assert updated_rule.json()["version"] == 2
    assert updated_rule.json()["notes"] == "Regra revisada."

    block_payload = {
        "rule_id": rule_data["id"],
        "theme": "identity",
        "potency_central": "Expressao vital intensa.",
        "poorly_expressed": "Impulsividade.",
        "well_expressed": "Coragem e presenca.",
        "complementary_axis": "Libra equilibra a afirmacao.",
        "challenges": "Aprender paciencia.",
        "integration_path": "Canalizar iniciativa com consciencia.",
        "keywords_json": ["lideranca", "iniciativa"],
        "interpretive_weight": 7.0,
        "editorial_notes": "Primeiro bloco.",
    }
    block_response = await client.post("/api/v1/editorial/blocks", json=block_payload)
    assert block_response.status_code == 201
    block_data = block_response.json()

    listed_blocks = await client.get(f"/api/v1/editorial/rules/{rule_data['id']}/blocks")
    assert listed_blocks.status_code == 200
    assert len(listed_blocks.json()) == 1

    updated_block = await client.patch(
        f"/api/v1/editorial/blocks/{block_data['id']}",
        json={"editorial_notes": "Bloco revisado."},
    )
    assert updated_block.status_code == 200
    assert updated_block.json()["editorial_notes"] == "Bloco revisado."

    deleted_block = await client.delete(f"/api/v1/editorial/blocks/{block_data['id']}")
    assert deleted_block.status_code == 204

    deleted_rule = await client.delete(f"/api/v1/editorial/rules/{rule_data['id']}")
    assert deleted_rule.status_code == 204

    deleted_source = await client.delete(f"/api/v1/editorial/sources/{source_data['id']}")
    assert deleted_source.status_code == 204
