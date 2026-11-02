import re
from typing import Any, Dict, List, Optional
import httpx

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest"

# Built-in fast cache for common lab reagents (instant demo & fallback resilience)
COMMON_LAB_REAGENTS: Dict[str, Dict[str, Any]] = {
    # Flammable Solvents & Organics
    "67-64-1": {"name": "Acetone", "cas": "67-64-1", "cid": 180, "h_codes": ["H225", "H319", "H336"]},
    "acetone": {"name": "Acetone", "cas": "67-64-1", "cid": 180, "h_codes": ["H225", "H319", "H336"]},
    "67-56-1": {"name": "Methanol", "cas": "67-56-1", "cid": 887, "h_codes": ["H225", "H301", "H311", "H331", "H370"]},
    "methanol": {"name": "Methanol", "cas": "67-56-1", "cid": 887, "h_codes": ["H225", "H301", "H311", "H331", "H370"]},
    "64-17-5": {"name": "Ethanol", "cas": "64-17-5", "cid": 702, "h_codes": ["H225", "H319"]},
    "ethanol": {"name": "Ethanol", "cas": "64-17-5", "cid": 702, "h_codes": ["H225", "H319"]},
    "67-63-0": {"name": "Isopropanol", "cas": "67-63-0", "cid": 3776, "h_codes": ["H225", "H319", "H336"]},
    "isopropanol": {"name": "Isopropanol", "cas": "67-63-0", "cid": 3776, "h_codes": ["H225", "H319", "H336"]},
    "75-05-8": {"name": "Acetonitrile", "cas": "75-05-8", "cid": 6342, "h_codes": ["H225", "H302", "H312", "H319", "H332"]},
    "acetonitrile": {"name": "Acetonitrile", "cas": "75-05-8", "cid": 6342, "h_codes": ["H225", "H302", "H312", "H319", "H332"]},
    "110-54-3": {"name": "Hexane", "cas": "110-54-3", "cid": 8058, "h_codes": ["H225", "H304", "H315", "H336", "H361", "H373", "H411"]},
    "hexane": {"name": "Hexane", "cas": "110-54-3", "cid": 8058, "h_codes": ["H225", "H304", "H315", "H336", "H361", "H373", "H411"]},
    "108-88-3": {"name": "Toluene", "cas": "108-88-3", "cid": 1140, "h_codes": ["H225", "H304", "H315", "H336", "H361", "H373"]},
    "toluene": {"name": "Toluene", "cas": "108-88-3", "cid": 1140, "h_codes": ["H225", "H304", "H315", "H336", "H361", "H373"]},
    "141-78-6": {"name": "Ethyl Acetate", "cas": "141-78-6", "cid": 8857, "h_codes": ["H225", "H319", "H336"]},
    "ethyl acetate": {"name": "Ethyl Acetate", "cas": "141-78-6", "cid": 8857, "h_codes": ["H225", "H319", "H336"]},
    "109-99-9": {"name": "Tetrahydrofuran (THF)", "cas": "109-99-9", "cid": 8028, "h_codes": ["H225", "H302", "H319", "H335", "H351"]},
    "tetrahydrofuran": {"name": "Tetrahydrofuran (THF)", "cas": "109-99-9", "cid": 8028, "h_codes": ["H225", "H302", "H319", "H335", "H351"]},
    "60-29-7": {"name": "Diethyl Ether", "cas": "60-29-7", "cid": 3283, "h_codes": ["H224", "H302", "H336"]},
    "diethyl ether": {"name": "Diethyl Ether", "cas": "60-29-7", "cid": 3283, "h_codes": ["H224", "H302", "H336"]},
    "64-19-7": {"name": "Acetic Acid (Glacial)", "cas": "64-19-7", "cid": 176, "h_codes": ["H226", "H314"]},
    "acetic acid": {"name": "Acetic Acid (Glacial)", "cas": "64-19-7", "cid": 176, "h_codes": ["H226", "H314"]},
    "121-44-8": {"name": "Triethylamine", "cas": "121-44-8", "cid": 8471, "h_codes": ["H225", "H302", "H311", "H314", "H331"]},
    "triethylamine": {"name": "Triethylamine", "cas": "121-44-8", "cid": 8471, "h_codes": ["H225", "H302", "H311", "H314", "H331"]},

    # Chlorinated & CMR Solvents
    "67-66-3": {"name": "Chloroform", "cas": "67-66-3", "cid": 6212, "h_codes": ["H302", "H315", "H319", "H331", "H336", "H351", "H361", "H372"]},
    "chloroform": {"name": "Chloroform", "cas": "67-66-3", "cid": 6212, "h_codes": ["H302", "H315", "H319", "H331", "H336", "H351", "H361", "H372"]},
    "75-09-2": {"name": "Dichloromethane (DCM)", "cas": "75-09-2", "cid": 6344, "h_codes": ["H315", "H319", "H336", "H351"]},
    "dichloromethane": {"name": "Dichloromethane (DCM)", "cas": "75-09-2", "cid": 6344, "h_codes": ["H315", "H319", "H336", "H351"]},
    "68-12-2": {"name": "Dimethylformamide (DMF)", "cas": "68-12-2", "cid": 6228, "h_codes": ["H226", "H312", "H319", "H332", "H360"]},
    "dimethylformamide": {"name": "Dimethylformamide (DMF)", "cas": "68-12-2", "cid": 6228, "h_codes": ["H226", "H312", "H319", "H332", "H360"]},

    # Corrosive Acids
    "7647-01-0": {"name": "Hydrochloric Acid", "cas": "7647-01-0", "cid": 313, "h_codes": ["H290", "H314", "H335"]},
    "hydrochloric acid": {"name": "Hydrochloric Acid", "cas": "7647-01-0", "cid": 313, "h_codes": ["H290", "H314", "H335"]},
    "7664-93-9": {"name": "Sulfuric Acid", "cas": "7664-93-9", "cid": 1118, "h_codes": ["H290", "H314"]},
    "sulfuric acid": {"name": "Sulfuric Acid", "cas": "7664-93-9", "cid": 1118, "h_codes": ["H290", "H314"]},
    "7664-38-2": {"name": "Phosphoric Acid", "cas": "7664-38-2", "cid": 1004, "h_codes": ["H290", "H314"]},
    "phosphoric acid": {"name": "Phosphoric Acid", "cas": "7664-38-2", "cid": 1004, "h_codes": ["H290", "H314"]},
    "76-05-1": {"name": "Trifluoroacetic Acid (TFA)", "cas": "76-05-1", "cid": 6422, "h_codes": ["H314", "H332", "H412"]},
    "trifluoroacetic acid": {"name": "Trifluoroacetic Acid (TFA)", "cas": "76-05-1", "cid": 6422, "h_codes": ["H314", "H332", "H412"]},

    # Corrosive Bases
    "1310-73-2": {"name": "Sodium Hydroxide", "cas": "1310-73-2", "cid": 14798, "h_codes": ["H290", "H314"]},
    "sodium hydroxide": {"name": "Sodium Hydroxide", "cas": "1310-73-2", "cid": 14798, "h_codes": ["H290", "H314"]},
    "1310-58-3": {"name": "Potassium Hydroxide", "cas": "1310-58-3", "cid": 14797, "h_codes": ["H290", "H302", "H314"]},
    "potassium hydroxide": {"name": "Potassium Hydroxide", "cas": "1310-58-3", "cid": 14797, "h_codes": ["H290", "H302", "H314"]},
    "1336-21-6": {"name": "Ammonium Hydroxide", "cas": "1336-21-6", "cid": 14923, "h_codes": ["H314", "H335", "H400"]},
    "ammonium hydroxide": {"name": "Ammonium Hydroxide", "cas": "1336-21-6", "cid": 14923, "h_codes": ["H314", "H335", "H400"]},

    # Oxidizers
    "7697-37-2": {"name": "Nitric Acid", "cas": "7697-37-2", "cid": 944, "h_codes": ["H272", "H290", "H314", "H330"]},
    "nitric acid": {"name": "Nitric Acid", "cas": "7697-37-2", "cid": 944, "h_codes": ["H272", "H290", "H314", "H330"]},
    "7722-84-1": {"name": "Hydrogen Peroxide", "cas": "7722-84-1", "cid": 784, "h_codes": ["H271", "H302", "H314", "H332"]},
    "hydrogen peroxide": {"name": "Hydrogen Peroxide", "cas": "7722-84-1", "cid": 784, "h_codes": ["H271", "H302", "H314", "H332"]},
    "7722-64-7": {"name": "Potassium Permanganate", "cas": "7722-64-7", "cid": 516875, "h_codes": ["H272", "H302", "H314", "H361", "H410"]},
    "potassium permanganate": {"name": "Potassium Permanganate", "cas": "7722-64-7", "cid": 516875, "h_codes": ["H272", "H302", "H314", "H361", "H410"]},
    "7601-90-3": {"name": "Perchloric Acid", "cas": "7601-90-3", "cid": 24247, "h_codes": ["H271", "H290", "H314"]},
    "perchloric acid": {"name": "Perchloric Acid", "cas": "7601-90-3", "cid": 24247, "h_codes": ["H271", "H290", "H314"]},

    # Acute Toxics
    "26628-22-8": {"name": "Sodium Azide", "cas": "26628-22-8", "cid": 33557, "h_codes": ["H300", "H310", "H330", "H410"]},
    "sodium azide": {"name": "Sodium Azide", "cas": "26628-22-8", "cid": 33557, "h_codes": ["H300", "H310", "H330", "H410"]},
    "151-50-8": {"name": "Potassium Cyanide", "cas": "151-50-8", "cid": 9032, "h_codes": ["H290", "H300", "H310", "H330", "H372", "H410"]},
    "potassium cyanide": {"name": "Potassium Cyanide", "cas": "151-50-8", "cid": 9032, "h_codes": ["H290", "H300", "H310", "H330", "H372", "H410"]},

    # Water-Reactives
    "7440-23-5": {"name": "Sodium Metal", "cas": "7440-23-5", "cid": 5360545, "h_codes": ["H260", "H314"]},
    "sodium metal": {"name": "Sodium Metal", "cas": "7440-23-5", "cid": 5360545, "h_codes": ["H260", "H314"]},
    "7646-69-7": {"name": "Sodium Hydride", "cas": "7646-69-7", "cid": 24758, "h_codes": ["H260", "H314"]},
    "sodium hydride": {"name": "Sodium Hydride", "cas": "7646-69-7", "cid": 24758, "h_codes": ["H260", "H314"]},
    "16853-85-3": {"name": "Lithium Aluminum Hydride (LAH)", "cas": "16853-85-3", "cid": 28112, "h_codes": ["H260", "H314"]},
    "lithium aluminum hydride": {"name": "Lithium Aluminum Hydride (LAH)", "cas": "16853-85-3", "cid": 28112, "h_codes": ["H260", "H314"]},

    # General Lab Salts & Buffers
    "7647-14-5": {"name": "Sodium Chloride", "cas": "7647-14-5", "cid": 5234, "h_codes": []},
    "sodium chloride": {"name": "Sodium Chloride", "cas": "7647-14-5", "cid": 5234, "h_codes": []},
    "144-55-8": {"name": "Sodium Bicarbonate", "cas": "144-55-8", "cid": 516892, "h_codes": []},
    "sodium bicarbonate": {"name": "Sodium Bicarbonate", "cas": "144-55-8", "cid": 516892, "h_codes": []}
}

def _extract_h_codes_from_json(data: Any) -> List[str]:
    """Recursively extracts all H-codes (H200-H499) from PubChem PUG View JSON."""
    raw_text = str(data)
    codes = set(re.findall(r"\bH[234]\d{2}[A-Za-z]*\b", raw_text))
    return sorted(list(codes))


async def fetch_chemical_data(query: str) -> Dict[str, Any]:
    """
    Fetches chemical name, CAS, CID, and GHS H-codes from local cache or PubChem API.
    Accepts either CAS number (e.g., '67-64-1') or chemical name (e.g., 'Acetone').
    """
    clean_query = query.strip()
    lookup_key = clean_query.lower()

    if lookup_key in COMMON_LAB_REAGENTS:
        return COMMON_LAB_REAGENTS[lookup_key].copy()

    is_cas = bool(re.match(r"^\d{2,7}-\d{2}-\d$", clean_query))

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Step 1: Resolve query to PubChem CID and Title
            prop_url = f"{PUBCHEM_BASE}/pug/compound/name/{clean_query}/property/Title/JSON"
            resp = await client.get(prop_url)
            if resp.status_code != 200:
                return {
                    "name": clean_query.title(),
                    "cas": clean_query if is_cas else "N/A",
                    "cid": None,
                    "h_codes": [],
                    "note": "Not found in PubChem; classified using name heuristics."
                }

            prop_data = resp.json()
            props = prop_data["PropertyTable"]["Properties"][0]
            cid = props["CID"]
            title = props.get("Title", clean_query.title())

            # Step 2: Fetch GHS Classification from PUG View
            ghs_url = f"{PUBCHEM_BASE}/pug_view/data/compound/{cid}/JSON?heading=GHS+Classification"
            ghs_resp = await client.get(ghs_url)
            h_codes: List[str] = []
            if ghs_resp.status_code == 200:
                h_codes = _extract_h_codes_from_json(ghs_resp.json())

            return {
                "name": title,
                "cas": clean_query if is_cas else "Verified via PubChem",
                "cid": cid,
                "h_codes": h_codes
            }
        except Exception:
            return {
                "name": clean_query.title(),
                "cas": clean_query if is_cas else "N/A",
                "cid": None,
                "h_codes": [],
                "note": "PubChem timeout; classified using name heuristics."
            }