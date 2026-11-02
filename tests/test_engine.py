from app.classifier import classify_chemical
from app.compatibility_engine import analyze_inventory, get_pair_compatibility


def test_acid_vs_base_classification_and_conflict():
    hcl = classify_chemical("Hydrochloric acid", ["H290", "H314", "H335"])
    naoh = classify_chemical("Sodium hydroxide", ["H290", "H314"])

    assert hcl["primary_group"] == "CORROSIVE_ACID"
    assert naoh["primary_group"] == "CORROSIVE_BASE"

    rule = get_pair_compatibility(hcl["primary_group"], naoh["primary_group"])
    assert rule["status"] == "incompatible"


def test_oxidizer_vs_flammable_conflict():
    acetone = classify_chemical("Acetone", ["H225", "H319", "H336"])
    h2o2 = classify_chemical("Hydrogen peroxide", ["H271", "H302", "H314"])

    assert acetone["primary_group"] == "FLAMMABLE"
    assert h2o2["primary_group"] == "OXIDIZER"

    inventory = [
        {"name": "Acetone", "cas": "67-64-1", **acetone},
        {"name": "Hydrogen peroxide", "cas": "7722-84-1", **h2o2}
    ]
    result = analyze_inventory(inventory)

    assert len(result["cabinets"]) == 2
    assert len(result["conflicts"]) == 1
    assert result["matrix"][0][1]["status"] == "incompatible"