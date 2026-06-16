"""
agents/intake_agent.py
----------------------
STEP 1: Intake Agent
Ingests and parses all 4 multi-modal inputs:
  1. priya_pt_invoice.png   → Vision (Gemini)
  2. aarav_mri_report.pdf   → PDF text extraction
  3. surgeon_estimate.jpg   → Vision (Gemini)
  4. user_query.txt         → NLP parsing
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_parser import parse_pt_invoice, parse_surgeon_estimate
from tools.pdf_parser import parse_mri_report, parse_user_query
from mock_apis.insurer1_plan_a import PLAN_A_CONFIG
from mock_apis.insurer2_plan_b import PLAN_B_CONFIG


def run_intake_agent(state: dict) -> dict:
    """
    Intake Agent: Parses all input files and loads insurance plan configurations.
    Returns updated state with parsed_documents and plan data.
    """
    raw_inputs = state.get("raw_inputs", {})
    base_dir = raw_inputs.get("base_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    inputs_dir = os.path.join(base_dir, "mock_inputs")

    parsed = {}
    messages = []
    errors = []

    # ── 1. Parse PT Invoice (Image → Vision) ──────────────────
    pt_invoice_path = raw_inputs.get("pt_invoice", os.path.join(inputs_dir, "priya_pt_invoice.png"))
    if os.path.exists(pt_invoice_path):
        print(f"  [DOC] Parsing PT invoice: {pt_invoice_path}")
        try:
            parsed["pt_invoice"] = parse_pt_invoice(pt_invoice_path)
            total = parsed["pt_invoice"].get("total_amount", 0)
            messages.append(f"[OK] PT Invoice parsed: ₹{total:,.0f} total for {parsed['pt_invoice'].get('patient_name', 'Unknown')}")
        except Exception as e:
            errors.append(f"PT invoice parse error: {str(e)}")
            # Use fallback
            parsed["pt_invoice"] = _fallback_pt_invoice()
            messages.append(f"[WARN]  PT invoice fallback used: {str(e)[:100]}")
    else:
        errors.append(f"PT invoice not found: {pt_invoice_path}")
        parsed["pt_invoice"] = _fallback_pt_invoice()
        messages.append(f"[WARN]  PT invoice not found, using mock data")

    # ── 2. Parse MRI Report (PDF → Text + Gemini) ─────────────
    mri_path = raw_inputs.get("mri_report", os.path.join(inputs_dir, "aarav_mri_report.pdf"))
    if os.path.exists(mri_path):
        print(f"  [DOC] Parsing MRI report: {mri_path}")
        try:
            parsed["mri_report"] = parse_mri_report(mri_path)
            diagnoses = parsed["mri_report"].get("diagnoses", [])
            messages.append(f"[OK] MRI Report parsed: {len(diagnoses)} diagnoses for {parsed['mri_report'].get('patient_name', 'Unknown')}")
        except Exception as e:
            errors.append(f"MRI report parse error: {str(e)}")
            parsed["mri_report"] = _fallback_mri_report()
            messages.append(f"[WARN]  MRI report fallback used: {str(e)[:100]}")
    else:
        errors.append(f"MRI report not found: {mri_path}")
        parsed["mri_report"] = _fallback_mri_report()
        messages.append(f"[WARN]  MRI report not found, using mock data")

    # ── 3. Parse Surgeon Estimate (Image → Vision) ─────────────
    surg_path = raw_inputs.get("surgeon_estimate", os.path.join(inputs_dir, "surgeon_estimate.jpg"))
    if os.path.exists(surg_path):
        print(f"  [DOC] Parsing surgeon estimate: {surg_path}")
        try:
            parsed["surgeon_estimate"] = parse_surgeon_estimate(surg_path)
            total = parsed["surgeon_estimate"].get("total_estimated_charge", 0)
            procs = len(parsed["surgeon_estimate"].get("procedure_codes", []))
            messages.append(f"[OK] Surgeon estimate parsed: ₹{total:,.0f} total, {procs} procedures")
        except Exception as e:
            errors.append(f"Surgeon estimate parse error: {str(e)}")
            parsed["surgeon_estimate"] = _fallback_surgeon_estimate()
            messages.append(f"[WARN]  Surgeon estimate fallback used: {str(e)[:100]}")
    else:
        errors.append(f"Surgeon estimate not found: {surg_path}")
        parsed["surgeon_estimate"] = _fallback_surgeon_estimate()
        messages.append(f"[WARN]  Surgeon estimate not found, using mock data")

    # ── 4. Parse User Query (Text → NLP) ──────────────────────
    query_path = raw_inputs.get("user_query", os.path.join(inputs_dir, "user_query.txt"))
    if os.path.exists(query_path):
        print(f"  [DOC] Parsing user query: {query_path}")
        try:
            parsed["user_query"] = parse_user_query(query_path)
            requests = parsed["user_query"].get("key_requests", [])
            messages.append(f"[OK] User query parsed: {len(requests)} key requests identified")
        except Exception as e:
            errors.append(f"User query parse error: {str(e)}")
            parsed["user_query"] = _fallback_user_query()
            messages.append(f"[WARN]  User query fallback used: {str(e)[:100]}")
    else:
        parsed["user_query"] = _fallback_user_query()
        messages.append(f"[WARN]  User query not found, using mock data")

    # ── 5. Load Insurance Plan Configurations ─────────────────
    messages.append("[OK] Loaded Plan A (Insurer1) configuration — Priya primary, Aarav dependent")
    messages.append("[OK] Loaded Plan B (Insurer2) configuration — Aarav primary, Priya dependent")

    print(f"  [OK] Intake complete: {len(parsed)} documents parsed, {len(errors)} errors")

    return {
        "parsed_documents": parsed,
        "plan_a_data": PLAN_A_CONFIG,
        "plan_b_data": PLAN_B_CONFIG,
        "messages": messages,
        "validation_errors": errors,
        "current_step": "intake_complete",
        "retry_count": 0,
    }


# ── Fallback Data ──────────────────────────────────────────────────────────────

def _fallback_pt_invoice():
    return {
        "clinic_name": "HealthFirst Physical Therapy Clinic, Mumbai",
        "patient_name": "Priya Sen",
        "invoice_number": "HFPT-2026-0447",
        "invoice_date": "2026-06-10",
        "dates_of_service": ["2026-05-15", "2026-05-22", "2026-05-29", "2026-06-05", "2026-06-10"],
        "referring_physician": "Dr. Ramesh Iyer MD",
        "line_items": [
            {"description": "PT Evaluation and Functional Assessment", "quantity": 1, "unit_price": 5000, "total": 5000, "cpt_code": None},
            {"description": "Therapeutic Exercise Sessions", "quantity": 5, "unit_price": 5000, "total": 25000, "cpt_code": None},
        ],
        "subtotal": 30000,
        "total_amount": 30000,
        "currency": "INR",
        "handwritten_notes": ["Treatment for chronic low back – physical therapy eval + exercise regimen. NO ICD codes listed."],
        "clinical_description": "Physical Therapy Evaluation and Therapeutic Exercise for chronic low back pain",
        "cpt_codes_present": False,
        "icd10_codes_present": False,
        "diagnosis_mentioned": "Chronic low back pain",
        "_source": "fallback",
    }


def _fallback_mri_report():
    return {
        "patient_name": "Aarav Sen",
        "patient_id": "APOL-MUM-2026-04872",
        "study_date": "2026-06-14",
        "report_date": "2026-06-15",
        "modality": "MRI 3.0 Tesla",
        "body_part": "Right Knee",
        "referring_physician": "Dr. Arjun Mehta, MS Ortho",
        "radiologist": "Dr. Kavitha Rao, FRCR",
        "facility": "Apollo Hospitals, Mumbai",
        "key_findings": [
            {"structure": "ACL", "finding": "Complete tear of ACL", "severity": "Complete", "is_critical": True},
            {"structure": "Medial Meniscus", "finding": "Grade III complex tear, posterior horn and body", "severity": "Severe", "is_critical": True},
        ],
        "impression": [
            "Complete tear of the anterior cruciate ligament (ACL) — Right Knee",
            "Complex tear of the medial meniscus — Grade III",
        ],
        "icd10_codes": [
            {"code": "M23.619", "description": "Other spontaneous disruption of ACL of right knee"},
            {"code": "M23.209", "description": "Derangement of medial meniscus, right knee"},
        ],
        "cpt_recommendations": [
            {"cpt_code": "29888", "description": "Arthroscopically aided ACL reconstruction"},
            {"cpt_code": "29881", "description": "Arthroscopy, knee, with meniscectomy"},
        ],
        "surgical_recommendation": True,
        "pre_auth_likely_required": True,
        "diagnoses": ["Complete ACL tear, right knee", "Medial meniscal tear (Grade III), right knee"],
        "_source": "fallback",
    }


def _fallback_surgeon_estimate():
    return {
        "surgeon_name": "Dr. Arjun Mehta, MS Orthopaedics",
        "hospital_facility": "Apollo Hospitals, Mumbai",
        "patient_name": "Aarav Sen",
        "patient_dob": "1988-03-15",
        "estimate_date": "2026-06-16",
        "procedure_codes": [
            {"cpt_code": "29888", "description": "Arthroscopically aided ACL reconstruction", "charge": 350000, "currency": "INR"},
            {"cpt_code": "29881", "description": "Arthroscopy, knee, surgical; with meniscectomy", "charge": 100000, "currency": "INR"},
        ],
        "total_estimated_charge": 450000,
        "currency": "INR",
        "pre_auth_noted": True,
        "notes": ["Pre-authorization required from insurance carrier prior to surgery"],
        "_source": "fallback",
    }


def _fallback_user_query():
    return {
        "speaker": "Aarav Sen",
        "key_requests": [
            "Determine COB order — which plan pays first for ACL surgery",
            "Determine COB order — which plan pays first for Priya's PT bills",
            "Calculate out-of-pocket expenses for both patients",
            "Generate pre-authorization letters for both insurers",
        ],
        "mentioned_patients": ["Aarav Sen", "Priya Sen"],
        "mentioned_plans": ["Insurer1 (Plan A)", "Insurer2 (Plan B)"],
        "mentioned_procedures": ["ACL surgery", "physical therapy"],
        "priority_concerns": ["Avoiding claim rejection", "Minimizing OOP costs", "Pre-auth letters"],
        "tone": "urgent",
        "_source": "fallback",
    }
