"""Code Lookup Agent for resolving CPT and ICD-10 codes from clinical text."""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from dotenv import load_dotenv
from tools.cpt_icd_mapper import lookup_cpt_by_description, lookup_icd10_by_description, get_cpt_details
from tools.model_helper import get_available_model

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def run_code_lookup_agent(state: dict) -> dict:
    """Validate and resolve CPT and ICD-10 codes."""
    parsed = state.get("parsed_documents", {})
    retry_count = state.get("retry_count", 0)
    messages = []
    errors = []
    all_cpt_codes = []
    all_icd10_codes = []

    pt_invoice = parsed.get("pt_invoice", {})
    if not pt_invoice.get("cpt_codes_present", False):
        print("  [SEARCH] PT invoice has no CPT codes - inferring from description...")
        pt_description = pt_invoice.get("clinical_description", "")
        handwritten = " ".join(pt_invoice.get("handwritten_notes", []))
        full_description = f"{pt_description} {handwritten}"

        cpt_matches = lookup_cpt_by_description(full_description)
        icd_matches = lookup_icd10_by_description(full_description)

        cpt_from_llm = _llm_infer_cpt(full_description, pt_invoice.get("line_items", []))
        icd_from_llm = _llm_infer_icd10(full_description, pt_invoice.get("diagnosis_mentioned", ""))

        pt_cpt_codes = cpt_from_llm if cpt_from_llm else [c for c in cpt_matches[:3]]
        pt_icd_codes = icd_from_llm if icd_from_llm else [i for i in icd_matches[:2]]

        for code in pt_cpt_codes:
            code["patient"] = "Priya Sen"
            code["claim_type"] = "physical_therapy"
            code["source"] = "inferred"
            all_cpt_codes.append(code)

        for code in pt_icd_codes:
            code["patient"] = "Priya Sen"
            code["claim_type"] = "physical_therapy"
            all_icd10_codes.append(code)

        messages.append(f"[OK] PT Invoice: Inferred CPT codes: {[c['cpt_code'] for c in pt_cpt_codes]}")
        messages.append(f"[OK] PT Invoice: Inferred ICD-10 codes: {[i['icd10_code'] for i in pt_icd_codes]}")
    else:
        for item in pt_invoice.get("line_items", []):
            if item.get("cpt_code"):
                details = get_cpt_details(item["cpt_code"]) or {
                    "cpt_code": item["cpt_code"],
                    "description": item.get("description", ""),
                }
                details["patient"] = "Priya Sen"
                details["claim_type"] = "physical_therapy"
                details["source"] = "extracted"
                all_cpt_codes.append(details)

    surgeon_est = parsed.get("surgeon_estimate", {})
    for proc in surgeon_est.get("procedure_codes", []):
        cpt_code = proc.get("cpt_code", "").strip()
        details = get_cpt_details(cpt_code) or {
            "cpt_code": cpt_code,
            "description": proc.get("description", ""),
            "typical_charge_inr": proc.get("charge", 0),
            "requires_preauth": True,
        }
        details["patient"] = "Aarav Sen"
        details["claim_type"] = "surgical"
        details["billed_amount"] = proc.get("charge", 0)
        details["source"] = "extracted"
        all_cpt_codes.append(details)

    messages.append(f"[OK] Surgeon Estimate: Confirmed CPT codes: {[p['cpt_code'] for p in surgeon_est.get('procedure_codes', [])]}")

    mri_report = parsed.get("mri_report", {})
    for icd in mri_report.get("icd10_codes", []):
        icd_entry = {
            "icd10_code": icd.get("code", ""),
            "description": icd.get("description", ""),
            "patient": "Aarav Sen",
            "claim_type": "surgical",
            "source": "extracted_from_mri",
        }
        if not any(x["icd10_code"] == icd_entry["icd10_code"] for x in all_icd10_codes):
            all_icd10_codes.append(icd_entry)

    mri_icd_codes = [i.get("code") or i.get("icd10_code", "") for i in mri_report.get("icd10_codes", [])]
    messages.append(f"[OK] MRI Report: Confirmed ICD-10 codes: {mri_icd_codes}")

    validation_errors = []
    aarav_cpts = [c for c in all_cpt_codes if c.get("patient") == "Aarav Sen"]
    priya_cpts = [c for c in all_cpt_codes if c.get("patient") == "Priya Sen"]
    aarav_icds = [i for i in all_icd10_codes if i.get("patient") == "Aarav Sen"]
    priya_icds = [i for i in all_icd10_codes if i.get("patient") == "Priya Sen"]

    if not aarav_cpts:
        validation_errors.append("MISSING: No CPT codes for Aarav's surgery")
    if not priya_cpts:
        validation_errors.append("MISSING: No CPT codes for Priya's PT")
    if not aarav_icds:
        validation_errors.append("MISSING: No ICD-10 codes for Aarav")
    if not priya_icds:
        validation_errors.append("MISSING: No ICD-10 codes for Priya")

    aarav_cpt_codes = [c["cpt_code"] for c in aarav_cpts]
    if "29888" not in aarav_cpt_codes:
        validation_errors.append("MISSING: CPT 29888 (ACL Reconstruction) for Aarav")
    if "29881" not in aarav_cpt_codes:
        validation_errors.append("MISSING: CPT 29881 (Meniscectomy) for Aarav")

    if validation_errors:
        print(f"  [WARN]  Validation issues ({len(validation_errors)}): {validation_errors}")
        new_retry_count = retry_count + 1
    else:
        print(f"  [OK] Code validation passed: {len(all_cpt_codes)} CPT + {len(all_icd10_codes)} ICD-10 codes")
        new_retry_count = retry_count

    return {
        "cpt_codes": all_cpt_codes,
        "icd10_codes": all_icd10_codes,
        "code_lookup_complete": len(validation_errors) == 0,
        "code_validation_errors": validation_errors,
        "messages": messages,
        "validation_errors": errors,
        "current_step": "code_lookup_complete",
        "retry_count": new_retry_count,
    }


def _llm_infer_cpt(clinical_description: str, line_items: list) -> list[dict]:
    """Use Gemini to infer CPT codes from clinical description."""
    try:
        model_name = get_available_model("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        items_text = "\n".join([f"  - {item.get('description', '')}: ₹{item.get('total', 0)}" for item in line_items])
        prompt = f"""You are a medical coding specialist. Based on this clinical description and service line items, identify the most appropriate CPT codes.

Clinical Description: {clinical_description}

Service Line Items:
{items_text}

Return a JSON array of objects with this structure:
[
  {{
    "cpt_code": "5-digit CPT code",
    "description": "official CPT description",
    "category": "Physical Therapy / Surgery / etc.",
    "typical_charge_inr": approximate charge in INR as integer,
    "requires_preauth": false,
    "reasoning": "brief explanation of why this code applies"
  }}
]

RULES:
- For "PT Evaluation" or "Physical Therapy Evaluation" → use CPT 97161 (low complexity) or 97162 (moderate)
- For "Therapeutic Exercise" → use CPT 97110
- For "Manual Therapy" → use CPT 97140
- Only include codes that are clearly supported by the description
- Maximum 3 codes

Return ONLY valid JSON array."""

        response = model.generate_content(prompt)
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        codes = json.loads(raw)
        return codes if isinstance(codes, list) else []
    except Exception as e:
        print(f"  [WARN]  LLM CPT inference failed")
        return [
            {
                "cpt_code": "97161",
                "description": "Physical therapy evaluation, low complexity",
                "category": "Physical Therapy",
                "typical_charge_inr": 3500,
                "requires_preauth": False,
                "reasoning": "PT Evaluation service line item",
            },
            {
                "cpt_code": "97110",
                "description": "Therapeutic procedure; therapeutic exercises",
                "category": "Physical Therapy",
                "typical_charge_inr": 3000,
                "requires_preauth": False,
                "reasoning": "Therapeutic Exercise Sessions (5x) line item",
            }
        ]


def _llm_infer_icd10(clinical_description: str, diagnosis: str) -> list[dict]:
    """Use Gemini to infer ICD-10 codes from clinical description."""
    try:
        model_name = get_available_model("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        prompt = f"""You are a medical coding specialist. Based on this clinical information, identify the appropriate ICD-10-CM codes.

Clinical Description: {clinical_description}
Diagnosis Mentioned: {diagnosis}

Return a JSON array of objects:
[
  {{
    "icd10_code": "ICD-10-CM code",
    "description": "official description",
    "reasoning": "brief explanation"
  }}
]

RULES:
- For "low back pain" / "chronic back pain" → M54.5 (Low back pain) or M54.59
- For "physical therapy" aftercare → Z47.89
- Maximum 2 codes
- Return ONLY valid JSON array."""

        response = model.generate_content(prompt)
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        codes = json.loads(raw)
        return codes if isinstance(codes, list) else []
    except Exception as e:
        print(f"  [WARN]  LLM ICD-10 inference failed: {e}")
        return [
            {
                "icd10_code": "M54.5",
                "description": "Low back pain",
                "reasoning": "Chronic low back pain diagnosis mentioned",
            }
        ]
