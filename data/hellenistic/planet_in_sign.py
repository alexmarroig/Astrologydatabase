"""Engine-ready Hellenistic `planet_in_sign` seed batch."""

PLANET_IN_SIGN_BATCH = [
    {
        "interpretation_rule": {
            "canonical_code": "sun_in_aries",
            "rule_type": "planet_in_sign",
            "subject_1_type": "planet",
            "subject_1_id": "sun",
            "subject_2_type": "sign",
            "subject_2_id": "aries",
            "system": "hellenistic",
            "base_weight": 0.9,
            "status": "validated",
            "version": 1,
        },
        "interpretation_block": {
            "theme": "identity",
            "core_statement": "Sun in Aries establishes authority through immediate action and direct assertion",
            "manifestation": "The native assumes leadership without delay, enters contests openly and defines status through visible initiative",
            "risk_expression": "Authority becomes forceful, judgment is executed too quickly and position is weakened by unnecessary conflict",
            "modifiers_json": [
                {
                    "type": "amplifier",
                    "condition": {
                        "type": "house",
                        "value": {
                            "category": "angular",
                        },
                    },
                    "effect": "increases visibility and dominance of authority",
                    "weight_delta": 0.2,
                },
                {
                    "type": "mitigator",
                    "condition": {
                        "type": "aspect",
                        "value": {
                            "aspect": "trine",
                            "planet": "jupiter",
                        },
                    },
                    "effect": "improves timing, legitimacy and strategic direction",
                    "weight_delta": -0.1,
                },
            ],
            "interpretive_weight": 0.9,
            "priority": 1,
        },
    },
    {
        "interpretation_rule": {
            "canonical_code": "moon_in_taurus",
            "rule_type": "planet_in_sign",
            "subject_1_type": "planet",
            "subject_1_id": "moon",
            "subject_2_type": "sign",
            "subject_2_id": "taurus",
            "system": "hellenistic",
            "base_weight": 0.88,
            "status": "validated",
            "version": 1,
        },
        "interpretation_block": {
            "theme": "identity",
            "core_statement": "Moon in Taurus secures life through continuity, retention and stable provision",
            "manifestation": "The native preserves resources, anchors routine in material steadiness and protects livelihood through what can be fed, held and maintained",
            "risk_expression": "Retention becomes stubborn possession, comfort blocks necessary movement and provision narrows into hoarding",
            "modifiers_json": [
                {
                    "type": "amplifier",
                    "condition": {
                        "type": "dignity",
                        "value": {
                            "state": "exaltation",
                            "planet": "moon",
                        },
                    },
                    "effect": "increases fertility, receptivity and dependable material support",
                    "weight_delta": 0.21,
                },
                {
                    "type": "redirector",
                    "condition": {
                        "type": "house",
                        "value": {
                            "house": 10,
                        },
                    },
                    "effect": "redirects stability toward public reputation, patronage and visible stewardship",
                    "weight_delta": 0.08,
                },
            ],
            "interpretive_weight": 0.88,
            "priority": 1,
        },
    },
    {
        "interpretation_rule": {
            "canonical_code": "mercury_in_gemini",
            "rule_type": "planet_in_sign",
            "subject_1_type": "planet",
            "subject_1_id": "mercury",
            "subject_2_type": "sign",
            "subject_2_id": "gemini",
            "system": "hellenistic",
            "base_weight": 0.87,
            "status": "validated",
            "version": 1,
        },
        "interpretation_block": {
            "theme": "identity",
            "core_statement": "Mercury in Gemini operates through division, comparison and rapid exchange",
            "manifestation": "The native gathers facts quickly, negotiates through speech and gains leverage by faster interpretation and agile communication",
            "risk_expression": "Speech scatters, judgment fragments and information is used without hierarchy or restraint",
            "modifiers_json": [
                {
                    "type": "amplifier",
                    "condition": {
                        "type": "dignity",
                        "value": {
                            "state": "domicile",
                            "planet": "mercury",
                        },
                    },
                    "effect": "increases speed, flexibility and verbal control",
                    "weight_delta": 0.19,
                },
                {
                    "type": "mitigator",
                    "condition": {
                        "type": "aspect",
                        "value": {
                            "aspect": "trine",
                            "planet": "saturn",
                        },
                    },
                    "effect": "improves order, memory and disciplined sequencing",
                    "weight_delta": -0.08,
                },
            ],
            "interpretive_weight": 0.87,
            "priority": 1,
        },
    },
    {
        "interpretation_rule": {
            "canonical_code": "venus_in_libra",
            "rule_type": "planet_in_sign",
            "subject_1_type": "planet",
            "subject_1_id": "venus",
            "subject_2_type": "sign",
            "subject_2_id": "libra",
            "system": "hellenistic",
            "base_weight": 0.89,
            "status": "validated",
            "version": 1,
        },
        "interpretation_block": {
            "theme": "identity",
            "core_statement": "Venus in Libra orders alliance through balance, reciprocity and formal agreement",
            "manifestation": "The native settles disputes by proportion, preserves bonds through fairness and strengthens position through mutual obligation and negotiated symmetry",
            "risk_expression": "Agreement becomes performance, judgment is surrendered to approval and harmony is preserved at the cost of truth",
            "modifiers_json": [
                {
                    "type": "amplifier",
                    "condition": {
                        "type": "dignity",
                        "value": {
                            "state": "domicile",
                            "planet": "venus",
                        },
                    },
                    "effect": "increases diplomatic power, social favor and ease in forming alliances",
                    "weight_delta": 0.18,
                },
                {
                    "type": "redirector",
                    "condition": {
                        "type": "rulership",
                        "value": {
                            "ruler": "venus",
                            "placement": {
                                "type": "house",
                                "value": 7,
                            },
                        },
                    },
                    "effect": "redirects relational skill toward marriage, contracts and negotiated partnerships",
                    "weight_delta": 0.07,
                },
            ],
            "interpretive_weight": 0.89,
            "priority": 1,
        },
    },
    {
        "interpretation_rule": {
            "canonical_code": "mars_in_scorpio",
            "rule_type": "planet_in_sign",
            "subject_1_type": "planet",
            "subject_1_id": "mars",
            "subject_2_type": "sign",
            "subject_2_id": "scorpio",
            "system": "hellenistic",
            "base_weight": 0.92,
            "status": "validated",
            "version": 1,
        },
        "interpretation_block": {
            "theme": "identity",
            "core_statement": "Mars in Scorpio acts through secrecy, penetration and controlled force",
            "manifestation": "The native applies hidden leverage, endures sustained conflict and secures outcomes through pressure, strategy and exact retaliation",
            "risk_expression": "Force turns vindictive, conflict is prolonged for domination and damage is inflicted through concealment",
            "modifiers_json": [
                {
                    "type": "amplifier",
                    "condition": {
                        "type": "dignity",
                        "value": {
                            "state": "domicile",
                            "planet": "mars",
                        },
                    },
                    "effect": "increases concentration, force and resistance to opposition",
                    "weight_delta": 0.2,
                },
                {
                    "type": "mitigator",
                    "condition": {
                        "type": "aspect",
                        "value": {
                            "aspect": "trine",
                            "planet": "jupiter",
                        },
                    },
                    "effect": "improves timing, lawfulness and strategic restraint",
                    "weight_delta": -0.1,
                },
            ],
            "interpretive_weight": 0.92,
            "priority": 1,
        },
    },
]
