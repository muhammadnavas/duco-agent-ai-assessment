"""
agents/preauth_check_agent.py
-----------------------------
STEP 3: Pre-Authorization Check Agent
Determines which CPT codes require pre-authorization from each insurance plan.
Queries both mock Plan A and Plan B APIs.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_apis.insurer1_plan_a import PLAN_A_CONFIG
from mock_apis.insurer2_plan_b import PLAN_B_CONFIG


PLAN_A_PREAUTH_CODES = set(PLAN_A_CONFIG["coverage"]["pre_authorization_required"])
PLAN_B_PREAUTH_CODES = set(PLAN_B_CONFIG["coverage"]["pre_authorization_required"])


def run_preauth_check_agent(state: dict) -> dict:
    """
    Pre-Auth Check Agent:
    - Check each CPT code against both Plan A and Plan B's pre-auth requirements
    - Determine overall pre-auth status
    - Flag which procedures need letters before claims can be submitted
    """
    cpt_codes = state.get("cpt_codes", [])
    messages = []
    preauth_required = {}

    print(f"  [SEARCH] Checking pre-auth for {len(cpt_codes)} CPT codes...")

    for cpt_entry in cpt_codes:
        cpt = cpt_entry.get("cpt_code", "")
        patient = cpt_entry.get("patient", "Unknown")
        claim_type = cpt_entry.get("claim_type", "")

        plan_a_required = cpt in PLAN_A_PREAUTH_CODES
        plan_b_required = cpt in PLAN_B_PREAUTH_CODES

        preauth_required[cpt] = {
            "cpt_code": cpt,
            "description": cpt_entry.get("description", ""),
            "patient": patient,
            "claim_type": claim_type,
            "plan_a_required": plan_a_required,
            "plan_b_required": plan_b_required,
            "plan_a_turnaround_days": PLAN_A_CONFIG["coverage"]["pre_auth_turnaround_days"] if plan_a_required else None,
            "plan_b_turnaround_days": PLAN_B_CONFIG["coverage"]["pre_auth_turnaround_days"] if plan_b_required else None,
            "either_required": plan_a_required or plan_b_required,
            "both_required": plan_a_required and plan_b_required,
        }

        status_a = "[WARN]  REQUIRED" if plan_a_required else "[OK] Not required"
        status_b = "[WARN]  REQUIRED" if plan_b_required else "[OK] Not required"
        print(f"  CPT {cpt} ({patient}): Plan A={status_a} | Plan B={status_b}")
        messages.append(f"CPT {cpt} pre-auth: Plan A → {'Required' if plan_a_required else 'Not Required'} | Plan B → {'Required' if plan_b_required else 'Not Required'}")

    any_required = any(v["either_required"] for v in preauth_required.values())
    all_required = all(v["either_required"] for v in preauth_required.values()) if preauth_required else False

    if not preauth_required or not any_required:
        status = "not_required"
        print("  [OK] No pre-authorization required for any procedure")
    elif all_required:
        status = "required"
        print(f"  [WARN]  Pre-authorization REQUIRED for all {len(preauth_required)} procedure(s)")
    else:
        status = "partial"
        print(f"  [WARN]  Pre-authorization REQUIRED for some procedures")

    surgical_codes = [cpt for cpt, v in preauth_required.items() if v["claim_type"] == "surgical"]
    pt_codes = [cpt for cpt, v in preauth_required.items() if v["claim_type"] == "physical_therapy"]

    messages.append(f"Summary: {len(surgical_codes)} surgical codes, {len(pt_codes)} PT codes checked")
    messages.append(f"Pre-auth status: {status.upper()}")

    return {
        "preauth_required": preauth_required,
        "preauth_status": status,
        "messages": messages,
        "current_step": "preauth_check_complete",
    }
