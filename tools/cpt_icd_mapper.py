"""
tools/cpt_icd_mapper.py
-----------------------
CPT and ICD-10 code lookup + inference tool.
Used by the code_lookup_agent to map clinical descriptions to codes.
"""
from typing import Optional

# ────────────────────────────────────────────────────────────
# CPT Code Reference Database
# ────────────────────────────────────────────────────────────
CPT_DATABASE = {
    # Physical Therapy
    "97161": {
        "description": "Physical therapy evaluation, low complexity",
        "category": "Physical Therapy",
        "typical_charge_inr": 3500,
        "keywords": ["PT evaluation", "physical therapy eval", "evaluation", "assessment", "functional assessment",
                     "low back pain eval", "musculoskeletal evaluation"],
        "requires_preauth": False,
    },
    "97162": {
        "description": "Physical therapy evaluation, moderate complexity",
        "category": "Physical Therapy",
        "typical_charge_inr": 4000,
        "keywords": ["PT evaluation moderate", "moderate complexity eval"],
        "requires_preauth": False,
    },
    "97163": {
        "description": "Physical therapy evaluation, high complexity",
        "category": "Physical Therapy",
        "typical_charge_inr": 4500,
        "keywords": ["PT evaluation high complexity"],
        "requires_preauth": False,
    },
    "97110": {
        "description": "Therapeutic procedure; therapeutic exercises",
        "category": "Physical Therapy",
        "typical_charge_inr": 3000,
        "keywords": ["therapeutic exercise", "exercise therapy", "strengthening", "therapeutic exercises",
                     "rehab exercises", "physical therapy exercises", "exercise regimen", "exercise sessions"],
        "requires_preauth": False,
    },
    "97140": {
        "description": "Manual therapy techniques",
        "category": "Physical Therapy",
        "typical_charge_inr": 2800,
        "keywords": ["manual therapy", "mobilization", "manipulation", "joint mobilization"],
        "requires_preauth": False,
    },
    "97530": {
        "description": "Therapeutic activities, direct patient contact",
        "category": "Physical Therapy",
        "typical_charge_inr": 2500,
        "keywords": ["therapeutic activities", "functional activities", "ADL training"],
        "requires_preauth": False,
    },
    # Orthopedic Surgery — Knee
    "29888": {
        "description": "Arthroscopically aided anterior cruciate ligament repair/augmentation or reconstruction",
        "category": "Orthopedic Surgery",
        "typical_charge_inr": 350000,
        "keywords": ["ACL reconstruction", "anterior cruciate ligament reconstruction", "ACL repair",
                     "ACL surgery", "arthroscopic ACL", "CPT 29888"],
        "requires_preauth": True,
    },
    "29881": {
        "description": "Arthroscopy, knee, surgical; with meniscectomy (medial OR lateral, including any meniscal shaving)",
        "category": "Orthopedic Surgery",
        "typical_charge_inr": 100000,
        "keywords": ["meniscectomy", "meniscus removal", "medial meniscectomy", "lateral meniscectomy",
                     "meniscal shaving", "knee arthroscopy meniscus", "CPT 29881"],
        "requires_preauth": True,
    },
    "29870": {
        "description": "Arthroscopy, knee, diagnostic",
        "category": "Orthopedic Surgery",
        "typical_charge_inr": 60000,
        "keywords": ["diagnostic arthroscopy", "knee scope", "diagnostic knee arthroscopy"],
        "requires_preauth": True,
    },
    "27447": {
        "description": "Arthroplasty, knee, condyle and plateau; medial AND lateral compartments",
        "category": "Orthopedic Surgery",
        "typical_charge_inr": 500000,
        "keywords": ["total knee replacement", "TKR", "knee arthroplasty"],
        "requires_preauth": True,
    },
}

# ────────────────────────────────────────────────────────────
# ICD-10 Code Reference Database
# ────────────────────────────────────────────────────────────
ICD10_DATABASE = {
    # Musculoskeletal — Back/Spine
    "M54.5": {
        "description": "Low back pain",
        "keywords": ["low back pain", "back pain", "lumbar pain", "LBP", "chronic back pain", "back ache",
                     "lumbar backache", "back problems"],
    },
    "M54.51": {
        "description": "Vertebrogenic low back pain",
        "keywords": ["vertebrogenic back pain", "disc back pain"],
    },
    "M54.59": {
        "description": "Other low back pain",
        "keywords": ["other back pain", "chronic low back"],
    },
    "M47.816": {
        "description": "Spondylosis without myelopathy or radiculopathy, lumbar region",
        "keywords": ["spondylosis", "lumbar spondylosis", "degenerative disc"],
    },
    # Musculoskeletal — Knee/ACL
    "M23.619": {
        "description": "Other spontaneous disruption of anterior cruciate ligament of right knee",
        "keywords": ["ACL tear", "ACL rupture", "anterior cruciate ligament tear", "ACL injury", "ACL disruption"],
    },
    "M23.209": {
        "description": "Derangement of unspecified meniscus due to old tear or injury, right knee",
        "keywords": ["meniscus tear", "medial meniscus tear", "meniscal tear", "meniscal injury"],
    },
    "M25.361": {
        "description": "Stiffness of right knee, not elsewhere classified",
        "keywords": ["knee stiffness", "restricted knee", "knee movement limitation"],
    },
    "S83.511A": {
        "description": "Sprain of anterior cruciate ligament of right knee, initial encounter",
        "keywords": ["ACL sprain", "knee sprain initial"],
    },
    # Physical Therapy Diagnoses
    "Z47.89": {
        "description": "Encounter for other orthopedic aftercare",
        "keywords": ["post-op care", "physical therapy aftercare", "rehabilitation"],
    },
    "M99.03": {
        "description": "Segmental and somatic dysfunction of lumbar region",
        "keywords": ["lumbar dysfunction", "somatic dysfunction lumbar"],
    },
}

# ────────────────────────────────────────────────────────────
# Functions
# ────────────────────────────────────────────────────────────

def lookup_cpt_by_description(description: str) -> list[dict]:
    """
    Fuzzy keyword match of a clinical description to CPT codes.
    Returns list of matching CPT entries sorted by relevance.
    """
    description_lower = description.lower()
    matches = []

    for code, data in CPT_DATABASE.items():
        score = 0
        for kw in data["keywords"]:
            if kw.lower() in description_lower:
                score += len(kw.split())  # longer keyword matches score higher
        if score > 0:
            matches.append({
                "cpt_code": code,
                "description": data["description"],
                "category": data["category"],
                "typical_charge_inr": data["typical_charge_inr"],
                "requires_preauth": data["requires_preauth"],
                "match_score": score,
            })

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches


def lookup_icd10_by_description(description: str) -> list[dict]:
    """
    Fuzzy keyword match of a clinical description to ICD-10 codes.
    Returns list of matching ICD-10 entries sorted by relevance.
    """
    description_lower = description.lower()
    matches = []

    for code, data in ICD10_DATABASE.items():
        score = 0
        for kw in data["keywords"]:
            if kw.lower() in description_lower:
                score += len(kw.split())
        if score > 0:
            matches.append({
                "icd10_code": code,
                "description": data["description"],
                "match_score": score,
            })

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches


def get_cpt_details(cpt_code: str) -> Optional[dict]:
    """Get full details for a specific CPT code."""
    data = CPT_DATABASE.get(cpt_code)
    if data:
        return {"cpt_code": cpt_code, **data}
    return None


def get_icd10_details(icd10_code: str) -> Optional[dict]:
    """Get full details for a specific ICD-10 code."""
    data = ICD10_DATABASE.get(icd10_code)
    if data:
        return {"icd10_code": icd10_code, **data}
    return None


def requires_preauth(cpt_code: str) -> bool:
    """Check if a CPT code requires pre-authorization."""
    data = CPT_DATABASE.get(cpt_code)
    return data.get("requires_preauth", False) if data else False


if __name__ == "__main__":
    # Quick test
    print("=== CPT Lookup Test ===")
    results = lookup_cpt_by_description("Physical Therapy Evaluation and Therapeutic Exercise for back pain")
    for r in results:
        print(f"  {r['cpt_code']}: {r['description']} (score: {r['match_score']})")

    print("\n=== ICD-10 Lookup Test ===")
    icd_results = lookup_icd10_by_description("chronic low back pain")
    for r in icd_results:
        print(f"  {r['icd10_code']}: {r['description']} (score: {r['match_score']})")
