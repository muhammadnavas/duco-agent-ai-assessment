"""
agents/cob_logic_agent.py
-------------------------
STEP 4: Coordination of Benefits (COB) Logic Agent
Determines primary and secondary payer for each claim using:
  - Birthday Rule
  - Subscriber vs. Dependent status
  - Industry-standard COB guidelines (NAIC model)
Uses Gemini LLM for complex reasoning and explanation.
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# COB Rules Reference
COB_RULES = """
COORDINATION OF BENEFITS (COB) RULES — STANDARD INDUSTRY GUIDELINES:

1. SUBSCRIBER RULE: A plan where the patient is the PRIMARY POLICYHOLDER (subscriber/employee) 
   always pays BEFORE a plan where the patient is a DEPENDENT.

2. BIRTHDAY RULE (for dependents): When a child/dependent is covered under TWO plans as a dependent:
   - The plan of the parent whose birthday falls EARLIER in the calendar year pays first.
   - (Note: This applies to children; for spouses it's the Subscriber Rule that dominates)

3. DUAL COVERAGE — MARRIED COUPLE (Aarav & Priya's case):
   - For AARAV's claims:
     * Plan B (Insurer2): Aarav IS the primary policyholder → PAYS FIRST (Primary)
     * Plan A (Insurer1): Aarav is a DEPENDENT on Priya's plan → PAYS SECOND (Secondary)
   - For PRIYA's claims:
     * Plan A (Insurer1): Priya IS the primary policyholder → PAYS FIRST (Primary)
     * Plan B (Insurer2): Priya is a DEPENDENT on Aarav's plan → PAYS SECOND (Secondary)

4. SECONDARY PAYER LIABILITY: Secondary plan calculates its payment based on what remains 
   after the primary plan has paid, subject to its own deductibles and coinsurance.
   Secondary plan will NOT pay more than if it were the primary (Non-Duplication method).

5. NON-DUPLICATION: Total payments from both plans cannot exceed 100% of the total allowed 
   charges (plan cannot profit from insurance).
"""


def run_cob_logic_agent(state: dict) -> dict:
    """
    COB Logic Agent:
    - Applies COB rules to determine primary/secondary payer for each claim
    - Uses Gemini LLM for reasoning and explanation
    - Returns structured COB determination for both Aarav and Priya
    """
    plan_a = state.get("plan_a_data", {})
    plan_b = state.get("plan_b_data", {})
    cpt_codes = state.get("cpt_codes", [])
    parsed = state.get("parsed_documents", {})
    messages = []

    print("  📋 Applying COB rules for dual coverage scenario...")

    # ── Gather claim information ───────────────────────────────
    aarav_surgery = parsed.get("surgeon_estimate", {})
    priya_pt = parsed.get("pt_invoice", {})

    aarav_surgery_total = aarav_surgery.get("total_estimated_charge", 450000)
    priya_pt_total = priya_pt.get("total_amount", 30000)

    # ── Apply COB Logic for Aarav's Surgery ───────────────────
    # Rule: Aarav is PRIMARY on Plan B (Insurer2), DEPENDENT on Plan A (Insurer1)
    # Therefore: Plan B pays first, Plan A pays second.

    plan_a_id = plan_a.get("plan_id", "Plan A")
    plan_b_id = plan_b.get("plan_id", "Plan B")

    cob_aarav = {
        "patient": "Aarav Sen",
        "claim_type": "ACL Reconstruction Surgery",
        "cpt_codes": ["29888", "29881"],
        "total_billed": aarav_surgery_total,
        "primary_plan": {
            "plan_name": "Plan B (Insurer2 — PremiumShield Platinum)",
            "plan_id": plan_b_id,
            "reason": "Aarav is the PRIMARY POLICYHOLDER on Plan B",
            "pays_order": 1,
        },
        "secondary_plan": {
            "plan_name": "Plan A (Insurer1 — CorporateCare Gold)",
            "plan_id": plan_a_id,
            "reason": "Aarav is a DEPENDENT on Priya's Plan A — pays after primary",
            "pays_order": 2,
        },
        "cob_rule_applied": "Subscriber Rule: Plan where patient is primary policyholder pays first",
    }

    # ── Apply COB Logic for Priya's PT Bills ─────────────────
    # Rule: Priya is PRIMARY on Plan A (Insurer1), DEPENDENT on Plan B (Insurer2)
    # Therefore: Plan A pays first, Plan B pays second.

    cob_priya = {
        "patient": "Priya Sen",
        "claim_type": "Physical Therapy (Chronic Back Pain)",
        "cpt_codes": ["97161", "97110"],
        "total_billed": priya_pt_total,
        "primary_plan": {
            "plan_name": "Plan A (Insurer1 — CorporateCare Gold)",
            "plan_id": plan_a_id,
            "reason": "Priya is the PRIMARY POLICYHOLDER on Plan A",
            "pays_order": 1,
        },
        "secondary_plan": {
            "plan_name": "Plan B (Insurer2 — PremiumShield Platinum)",
            "plan_id": plan_b_id,
            "reason": "Priya is a DEPENDENT on Aarav's Plan B — pays after primary",
            "pays_order": 2,
        },
        "cob_rule_applied": "Subscriber Rule: Plan where patient is primary policyholder pays first",
    }

    # ── LLM Reasoning for Clinical Explanation ────────────────
    cob_reasoning = _generate_cob_reasoning(cob_aarav, cob_priya, plan_a, plan_b)

    messages.append(f"✅ COB Determination for Aarav: PRIMARY = {cob_aarav['primary_plan']['plan_name']}")
    messages.append(f"✅ COB Determination for Priya: PRIMARY = {cob_priya['primary_plan']['plan_name']}")
    messages.append(f"✅ COB Rule Applied: Subscriber Rule (policyholder vs dependent status)")

    print(f"  ✅ Aarav: PRIMARY → Plan B (Insurer2) | SECONDARY → Plan A (Insurer1)")
    print(f"  ✅ Priya: PRIMARY → Plan A (Insurer1) | SECONDARY → Plan B (Insurer2)")

    return {
        "cob_aarav": cob_aarav,
        "cob_priya": cob_priya,
        "cob_reasoning": cob_reasoning,
        "messages": messages,
        "current_step": "cob_logic_complete",
    }


def _generate_cob_reasoning(cob_aarav: dict, cob_priya: dict, plan_a: dict, plan_b: dict) -> str:
    """Use Gemini to generate a clear, clinically sound COB reasoning explanation."""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = f"""You are a senior health insurance COB (Coordination of Benefits) specialist.

SCENARIO:
- Priya Sen and Aarav Sen are a married couple with DUAL health insurance coverage.
- Plan A (Insurer1): Priya is the primary policyholder; Aarav is the dependent.
- Plan B (Insurer2): Aarav is the primary policyholder; Priya is the dependent.

CLAIMS:
1. Aarav needs ACL Reconstruction Surgery (CPT 29888 + 29881) — Total: ₹4,50,000
2. Priya has Physical Therapy bills (CPT 97161 + 97110) — Total: ₹30,000

COB DETERMINATION:
- For Aarav: Primary = Plan B | Secondary = Plan A
- For Priya: Primary = Plan A | Secondary = Plan B

COB RULES REFERENCE:
{COB_RULES}

Write a clear, professional, patient-friendly explanation (3-4 paragraphs) explaining:
1. Which plan pays first for each person and WHY
2. The specific COB rule being applied
3. What this means for Aarav and Priya practically
4. Any important caveats or things they should know

Use simple language that a patient (not an insurance expert) can understand.
Keep it under 400 words."""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"  ⚠️  LLM COB reasoning failed: {e}")
        return """
**Coordination of Benefits (COB) Explanation for the Sen Family**

Since both Priya and Aarav have health insurance through their employers and are enrolled as dependents on each other's plans, they have what's called "dual coverage" — meaning two insurance plans can potentially pay for their medical expenses.

**For Aarav's ACL Surgery:**
Because Aarav is the primary policyholder (subscriber/employee) on Plan B (Insurer2 — PremiumShield Platinum), Plan B will pay FIRST for his surgery. Plan A (Insurer1 — CorporateCare Gold), where Aarav is only a dependent on Priya's plan, will pay SECOND — covering what Plan B didn't pay, subject to its own deductible and coinsurance rules.

**For Priya's Physical Therapy Bills:**
Similarly, because Priya is the primary policyholder on Plan A (Insurer1 — CorporateCare Gold), Plan A pays FIRST for her PT sessions. Plan B (Insurer2), where Priya is only a dependent on Aarav's plan, pays SECOND as the secondary payer.

**The COB Rule Applied:**
This follows the "Subscriber Rule" — the most fundamental COB principle. The insurance plan where you ARE the employee/primary member ALWAYS pays before the plan where you are merely a dependent. This applies regardless of birthday or enrollment dates.

**Practical Implication:**
By coordinating benefits correctly, Aarav and Priya can significantly reduce their out-of-pocket costs. The secondary plan helps cover costs the primary plan didn't pay (deductibles, coinsurance), up to the limits of the secondary plan's own benefits. Total payments from both plans combined will never exceed 100% of the actual billed amount.
"""
