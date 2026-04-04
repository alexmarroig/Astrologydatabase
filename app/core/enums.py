"""
Domain enumerations for the astrological system.

These enums represent the formal ontological vocabulary of the system.
They are used in SQLAlchemy models, Pydantic schemas, and business logic.
All string values use snake_case for database compatibility.
"""

from __future__ import annotations

import enum


# ── Astrological Ontology ─────────────────────────────────────────────────────

class ElementType(str, enum.Enum):
    """Classical four-element taxonomy."""
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class ModalityType(str, enum.Enum):
    """Three-modality (quadruplicity) taxonomy."""
    CARDINAL = "cardinal"
    FIXED = "fixed"
    MUTABLE = "mutable"


class PolarityType(str, enum.Enum):
    """Yin/Yang polarity classification."""
    YANG = "yang"    # Active, masculine, fire/air signs
    YIN = "yin"      # Receptive, feminine, earth/water signs


class BodyCategory(str, enum.Enum):
    """Classification of celestial bodies and points."""
    PERSONAL = "personal"          # Sun, Moon, Mercury, Venus, Mars
    SOCIAL = "social"              # Jupiter, Saturn
    TRANSPERSONAL = "transpersonal"  # Uranus, Neptune, Pluto
    NODE = "node"                  # North Node, South Node
    ASTEROID = "asteroid"          # Chiron, Vesta, etc.
    ANGLE = "angle"               # ASC, MC, DSC, IC
    PART = "part"                 # Arabic Parts (Part of Fortune, etc.)
    HYPOTHETICAL = "hypothetical"  # Lilith, Black Moon, etc.


class HouseSystemType(str, enum.Enum):
    """Supported house division systems."""
    PLACIDUS = "placidus"          # Default — most common in modern western
    KOCH = "koch"                  # Popular in German-speaking countries
    EQUAL = "equal"                # Equal 30° houses from ASC
    WHOLE_SIGN = "whole_sign"      # Ancient — each sign = one house
    REGIOMONTANUS = "regiomontanus"
    CAMPANUS = "campanus"
    PORPHYRY = "porphyry"


class HousePosition(str, enum.Enum):
    """Angular classification of houses."""
    ANGULAR = "angular"          # Houses 1, 4, 7, 10 — strongest
    SUCCEDENT = "succedent"      # Houses 2, 5, 8, 11 — medium
    CADENT = "cadent"            # Houses 3, 6, 9, 12 — weakest


class AspectQuality(str, enum.Enum):
    """Classification by tradition vs. minor status."""
    MAJOR = "major"    # Conjunction, Opposition, Trine, Square, Sextile
    MINOR = "minor"    # Quincunx, Semisextile, Semisquare, Sesquiquadrate
    SPECIAL = "special"  # Yod legs, etc.


class AspectNature(str, enum.Enum):
    """Traditional nature of the aspect."""
    HARMONIC = "harmonic"    # Trine, Sextile
    TENSE = "tense"          # Square, Opposition
    NEUTRAL = "neutral"      # Conjunction (depends on planets)
    MIXED = "mixed"          # Quincunx — tension + adjustment


class DignityType(str, enum.Enum):
    """Essential dignities and debilities."""
    DOMICILE = "domicile"        # Strongest dignity — own home
    EXALTATION = "exaltation"    # Second best dignity
    PEREGRINE = "peregrine"      # No dignity or debility (neutral)
    EXILE = "exile"              # Detriment — opposite of domicile
    FALL = "fall"                # Opposite of exaltation


# ── Editorial Domain ──────────────────────────────────────────────────────────

class SchoolType(str, enum.Enum):
    """Astrological school / interpretive tradition."""
    LUZ_E_SOMBRA = "luz_e_sombra"      # Claudia Lisboa — primary school
    HUMANISTIC = "humanistic"           # Dane Rudhyar lineage
    TRADITIONAL = "traditional"         # Classical/Hellenistic traditional
    MODERN = "modern"                   # 20th century psychological
    HELLENISTIC = "hellenistic"         # Ancient Greek/Hellenistic
    PSYCHOLOGICAL = "psychological"     # Jung-influenced
    EVOLUTIONARY = "evolutionary"       # Jeffrey Wolf Green lineage


class RuleType(str, enum.Enum):
    """Type of astrological factor described by an interpretation rule."""
    PLANET_IN_SIGN = "planet_in_sign"          # e.g., Sun in Scorpio
    PLANET_IN_HOUSE = "planet_in_house"        # e.g., Moon in House 4
    ASPECT_PLANET_PLANET = "aspect_planet_planet"  # e.g., Sun square Saturn
    ASPECT_PLANET_ANGLE = "aspect_planet_angle"   # e.g., Mars conjunct ASC
    RULER_IN_HOUSE = "ruler_in_house"          # e.g., Ruler of H7 in H12
    RULER_IN_SIGN = "ruler_in_sign"            # e.g., Ruler of H10 in Aries
    DIGNITY = "dignity"                        # e.g., Venus in domicile
    RETROGRADE = "retrograde"                  # e.g., Mercury retrograde
    STELLIUM = "stellium"                      # 3+ planets in one sign/house
    ELEMENT_PREDOMINANCE = "element_predominance"  # e.g., Fire dominant
    MODALITY_PREDOMINANCE = "modality_predominance"
    PATTERN = "pattern"                        # T-square, Grand Trine, Yod, etc.
    MISSING_ELEMENT = "missing_element"        # No planets in Fire, etc.
    CHART_RULER = "chart_ruler"               # Overall chart ruler themes


class SubjectType(str, enum.Enum):
    """
    Type of entity referenced by subject_a, subject_b, subject_c
    in an interpretation rule.
    This enables generic foreign key semantics without actual FK constraints.
    """
    BODY = "body"          # References bodies table
    SIGN = "sign"          # References signs table
    HOUSE = "house"        # References houses table (by number or id)
    ASPECT = "aspect"      # References aspects table
    ANGLE = "angle"        # References angles table
    ELEMENT = "element"    # References element enum value
    MODALITY = "modality"  # References modality enum value
    DIGNITY = "dignity"    # References dignity type enum
    PATTERN = "pattern"    # References named aspect pattern
    NONE = "none"          # No subject


class RuleStatus(str, enum.Enum):
    """Editorial workflow status for interpretation rules."""
    DRAFT = "draft"           # Initial state — created, not reviewed
    REVIEW = "review"         # Submitted for editorial review
    APPROVED = "approved"     # Reviewed and approved, not yet published
    PUBLISHED = "published"   # Live — used in synthesis
    DEPRECATED = "deprecated" # Retired — preserved for history, not used


class SourceTrustLevel(str, enum.Enum):
    """Editorial trust level for reference sources."""
    PRIMARY = "primary"      # Main authoritative sources for the school
    SECONDARY = "secondary"  # Supporting / complementary sources
    REFERENCE = "reference"  # Background reference material


class InterpretiveTheme(str, enum.Enum):
    """
    High-level thematic area for interpretation blocks.
    Used to group and prioritize interpretive content in synthesis.
    """
    IDENTITY = "identity"          # Self-concept, ego, life purpose
    EMOTIONAL = "emotional"        # Inner life, emotional patterns, needs
    RELATIONAL = "relational"      # Partnerships, relationships, other
    VOCATIONAL = "vocational"      # Career, calling, public life
    SHADOW = "shadow"              # Unconscious patterns, complexes
    BODY = "body"                  # Physical body, health, vitality
    SPIRITUAL = "spiritual"        # Transcendence, meaning, soul
    FINANCIAL = "financial"        # Resources, values, material security
    MENTAL = "mental"              # Mind, communication, learning
    FAMILY = "family"              # Roots, ancestry, home
    SOCIAL = "social"              # Community, ideals, friendship
    TRANSFORMATION = "transformation"  # Crisis, death/rebirth, depth
