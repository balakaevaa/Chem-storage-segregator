import re
from typing import Dict, List, Set

# Mapping of GHS Hazard Codes to Primary Storage Groups
WATER_REACTIVE_CODES = {"H250", "H260", "H261"}
OXIDIZER_CODES = {"H270", "H271", "H272", "H240", "H241", "H242"}
FLAMMABLE_CODES = {"H220", "H221", "H222", "H224", "H225", "H226", "H228", "H251", "H252"}
ACUTE_TOXIC_CODES = {"H300", "H301", "H310", "H311", "H330", "H331"}
CORROSIVE_CODES = {"H290", "H314", "H318"}
HEALTH_HAZARD_CODES = {"H340", "H341", "H350", "H351", "H360", "H361", "H370", "H372"}

BASE_KEYWORDS = [
    r"\bhydroxide\b", r"\bammonia\b", r"\bammonium hydroxide\b", r"\bamine\b",
    r"\bethylamine\b", r"\btriethylamine\b", r"\bpyridine\b", r"\bcarbonate\b",
    r"\bbicarbonate\b", r"\bhydride\b", r"\bmethoxide\b", r"\bethoxide\b",
    r"\btert-butoxide\b", r"\bhypochlorite\b", r"\bkoh\b", r"\bnaoh\b", r"\blioh\b"
]

ACID_KEYWORDS = [
    r"\bacid\b", r"\banhydride\b", r"\bacyl chloride\b", r"\bchloride\b",
    r"\bhcl\b", r"\bh2so4\b", r"\bhno3\b", r"\btriflate\b", r"\bphenol\b"
]


def _normalize_h_codes(raw_codes: List[str]) -> Set[str]:
    """Extracts clean base H-codes (e.g., 'H301+H311' -> {'H301', 'H311'}, 'H350i' -> 'H350')."""
    normalized = set()
    for code in raw_codes:
        matches = re.findall(r"H\d{3}", code.upper())
        normalized.update(matches)
    return normalized


def _detect_acid_or_base(name: str, description: str = "") -> str:
    """Distinguishes between corrosive acids and bases using chemical nomenclature."""
    text = f"{name} {description}".lower()
    for pattern in BASE_KEYWORDS:
        if re.search(pattern, text):
            return "CORROSIVE_BASE"
    for pattern in ACID_KEYWORDS:
        if re.search(pattern, text):
            return "CORROSIVE_ACID"
    # Default corrosive fallback to acid cabinet with secondary inspection note
    return "CORROSIVE_ACID"


def classify_chemical(name: str, h_codes: List[str], description: str = "") -> Dict[str, object]:
    """
    Assigns a primary storage group and secondary hazard flags based on GHS H-codes
    following international chemical segregation hierarchy (OSHA / TRGS 510).
    """
    codes = _normalize_h_codes(h_codes)
    text_lower = f"{name} {description}".lower()
    secondary_flags = []

    # Collect all applicable hazard categories for transparency
    if codes & WATER_REACTIVE_CODES:
        secondary_flags.append("Water-Reactive")
    if codes & OXIDIZER_CODES or "nitric acid" in text_lower or "perchloric acid" in text_lower or "hydrogen peroxide" in text_lower:
        secondary_flags.append("Oxidizer")
    if codes & FLAMMABLE_CODES:
        secondary_flags.append("Flammable")
    if codes & ACUTE_TOXIC_CODES:
        secondary_flags.append("Acute Toxic")
    if codes & CORROSIVE_CODES or "acid" in text_lower or "hydroxide" in text_lower:
        secondary_flags.append("Corrosive")
    if codes & HEALTH_HAZARD_CODES:
        secondary_flags.append("CMR / Chronic Hazard")

    # Determine Primary Storage Group by strict safety priority hierarchy:
    # 1. Water-Reactive
    if codes & WATER_REACTIVE_CODES:
        primary_group = "WATER_REACTIVE"
    # 2. Oxidizers (Note: concentrated oxidizing acids like Nitric Acid are flagged as Oxidizers/Acids)
    elif codes & OXIDIZER_CODES:
        primary_group = "OXIDIZER"
    # 3. Flammables (Note: volatile organic acids like Acetic Acid or amines like Triethylamine go to Flammables if H225/H226)
    elif codes & FLAMMABLE_CODES:
        primary_group = "FLAMMABLE"
    # 4. Corrosives (Split into Acids and Bases before Acute Toxic for standard mineral acids/bases like HCl, H2SO4, NaOH)
    elif (codes & CORROSIVE_CODES) and any(k in text_lower for k in ["acid", "hydroxide", "ammonia", "anhydride"]):
        primary_group = _detect_acid_or_base(name, description)
    # 5. Acute Toxics
    elif codes & ACUTE_TOXIC_CODES:
        primary_group = "ACUTE_TOXIC"
    # 6. Remaining Corrosives
    elif codes & CORROSIVE_CODES:
        primary_group = _detect_acid_or_base(name, description)
    # 7. Chronic Health Hazards
    elif codes & HEALTH_HAZARD_CODES:
        primary_group = "HEALTH_HAZARD"
    # 8. Fallback by name heuristics if PubChem has missing GHS tags for common acids/bases
    elif "hydroxide" in text_lower:
        primary_group = "CORROSIVE_BASE"
    elif "acid" in text_lower and "amino acid" not in text_lower and "nucleic acid" not in text_lower:
        primary_group = "CORROSIVE_ACID"
    else:
        primary_group = "GENERAL_STORAGE"

    return {
        "primary_group": primary_group,
        "normalized_h_codes": sorted(list(codes)),
        "secondary_flags": secondary_flags if secondary_flags else ["Low Hazard"]
    }