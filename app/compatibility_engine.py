import json
from pathlib import Path
from typing import Any, Dict, List

RULES_PATH = Path(__file__).parent / "data" / "storage_rules.json"

with open(RULES_PATH, "r", encoding="utf-8") as f:
    STORAGE_DATA = json.load(f)

STORAGE_GROUPS = STORAGE_DATA["storage_groups"]
COMPATIBILITY_MATRIX = STORAGE_DATA["compatibility_matrix"]


def get_pair_compatibility(group_a: str, group_b: str) -> Dict[str, str]:
    """Returns compatibility status and reason for two storage groups."""
    if group_a in COMPATIBILITY_MATRIX and group_b in COMPATIBILITY_MATRIX[group_a]:
        return COMPATIBILITY_MATRIX[group_a][group_b]
    if group_b in COMPATIBILITY_MATRIX and group_a in COMPATIBILITY_MATRIX[group_b]:
        return COMPATIBILITY_MATRIX[group_b][group_a]
    return {
        "status": "caution",
        "reason": "Verify specific SDS storage requirements before co-locating."
    }


def analyze_inventory(chemicals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Takes a list of classified chemical dicts and generates:
    1. Enriched chemical list with cabinet metadata
    2. N x N pairwise compatibility matrix
    3. Segregated storage cabinets with assigned chemicals
    4. Critical conflict alerts
    """
    enriched_chemicals = []
    cabinets_map: Dict[str, Dict[str, Any]] = {}

    for chem in chemicals:
        group_key = chem["primary_group"]
        group_info = STORAGE_GROUPS.get(group_key, STORAGE_GROUPS["GENERAL_STORAGE"])

        enriched = {
            **chem,
            "group_title": group_info["title"],
            "cabinet": group_info["cabinet"],
            "badge_color": group_info["badge_color"],
            "priority": group_info["priority"]
        }
        enriched_chemicals.append(enriched)

        if group_key not in cabinets_map:
            cabinets_map[group_key] = {
                "group_key": group_key,
                "cabinet_name": group_info["cabinet"],
                "group_title": group_info["title"],
                "description": group_info["description"],
                "badge_color": group_info["badge_color"],
                "priority": group_info["priority"],
                "chemicals": []
            }
        cabinets_map[group_key]["chemicals"].append(enriched)

    # Sort cabinets by safety priority (1 = highest hazard)
    sorted_cabinets = sorted(cabinets_map.values(), key=lambda x: x["priority"])

    # Build N x N compatibility matrix and collect red conflict alerts
    matrix = []
    conflicts = []
    n = len(enriched_chemicals)

    for i in range(n):
        row = []
        for j in range(n):
            chem_a = enriched_chemicals[i]
            chem_b = enriched_chemicals[j]

            if i == j:
                cell = {
                    "status": "self",
                    "reason": "Same chemical substance."
                }
            else:
                pair_rule = get_pair_compatibility(chem_a["primary_group"], chem_b["primary_group"])
                cell = {
                    "status": pair_rule["status"],
                    "reason": pair_rule["reason"]
                }
                if i < j and pair_rule["status"] == "incompatible":
                    conflicts.append({
                        "chem_a": chem_a["name"],
                        "chem_b": chem_b["name"],
                        "group_a": chem_a["group_title"],
                        "group_b": chem_b["group_title"],
                        "reason": pair_rule["reason"]
                    })
            row.append(cell)
        matrix.append(row)

    return {
        "chemicals": enriched_chemicals,
        "matrix": matrix,
        "cabinets": sorted_cabinets,
        "conflicts": conflicts
    }