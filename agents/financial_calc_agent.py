"""
agents/financial_calc_agent.py
------------------------------
STEP 5: Financial Calculation Agent
Performs precise COB financial calculations:
  - Applies deductibles (primary plan first)
  - Calculates coinsurance splits
  - Applies secondary plan deductible to remaining balance
  - Computes out-of-pocket totals
  - Calculates savings vs. single-plan coverage
All amounts in Indian Rupees (INR).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PLAN_A_ALLOWED = {
    "29888": 320000,   # ACL Reconstruction
    "29881": 90000,    # Meniscectomy
    "97161": 3500,     # PT Evaluation
    "97110": 3000,     # Therapeutic Exercise (per session)
}
PLAN_B_ALLOWED = {
    "29888": 330000,   # ACL Reconstruction
    "29881": 92000,    # Meniscectomy
    "97161": 3800,     # PT Evaluation
    "97110": 3200,     # Therapeutic Exercise (per session)
}


def run_financial_calc_agent(state: dict) -> dict:
    """
    Financial Calculation Agent:
    Performs step-by-step COB financial math for both claims.
    """
    plan_a = state.get("plan_a_data", {})
    plan_b = state.get("plan_b_data", {})
    cob_aarav = state.get("cob_aarav", {})
    cob_priya = state.get("cob_priya", {})
    parsed = state.get("parsed_documents", {})
    messages = []

    ben_a = plan_a.get("benefits", {})
    ben_b = plan_b.get("benefits", {})

    print("  [CALC] Calculating Aarav's surgery costs (Primary: Plan B, Secondary: Plan A)...")

    plan_b_deductible_aarav = ben_b["annual_deductible_individual"]
    plan_b_deductible_met_aarav = ben_b.get("deductible_met_aarav", 0)
    plan_b_deductible_remaining = max(0, plan_b_deductible_aarav - plan_b_deductible_met_aarav)

    allowed_29888_b = PLAN_B_ALLOWED["29888"]   # ₹3,30,000
    allowed_29881_b = PLAN_B_ALLOWED["29881"]   # ₹92,000
    total_allowed_b = allowed_29888_b + allowed_29881_b  # ₹4,22,000

    plan_b_deductible_applied = min(plan_b_deductible_remaining, total_allowed_b)
    after_deductible_b = total_allowed_b - plan_b_deductible_applied

    plan_b_pays_coinsurance = round(after_deductible_b * ben_b["coinsurance_plan_pays"], 2)
    plan_b_member_coinsurance = round(after_deductible_b * ben_b["coinsurance_member_pays"], 2)

    plan_b_total_pays = plan_b_pays_coinsurance
    plan_b_member_oop_primary = plan_b_deductible_applied + plan_b_member_coinsurance

    plan_a_deductible_aarav = ben_a["annual_deductible_individual"]
    plan_a_deductible_met_aarav = ben_a.get("deductible_met_aarav", 0)
    plan_a_deductible_remaining = max(0, plan_a_deductible_aarav - plan_a_deductible_met_aarav)

    allowed_29888_a = PLAN_A_ALLOWED["29888"]   # ₹3,20,000
    allowed_29881_a = PLAN_A_ALLOWED["29881"]   # ₹90,000
    total_allowed_a = allowed_29888_a + allowed_29881_a  # ₹4,10,000

    primary_paid_plan_b = plan_b_total_pays

    plan_a_secondary_allowed = total_allowed_a  # Plan A's view of total allowed

    plan_a_deductible_applied_secondary = min(plan_a_deductible_remaining, plan_a_secondary_allowed)
    after_deductible_a_secondary = plan_a_secondary_allowed - plan_a_deductible_applied_secondary

    plan_a_hypothetical_primary_pay = round(after_deductible_a_secondary * ben_a["coinsurance_plan_pays"], 2)

    billed_total_aarav = parsed.get("surgeon_estimate", {}).get("total_estimated_charge", 450000)
    remaining_after_primary = max(0, billed_total_aarav - plan_b_total_pays)

    plan_a_secondary_pays = min(plan_a_hypothetical_primary_pay, remaining_after_primary)
    plan_a_secondary_pays = round(plan_a_secondary_pays, 2)

    aarav_oop = round(billed_total_aarav - plan_b_total_pays - plan_a_secondary_pays, 2)
    aarav_oop = max(0, aarav_oop)

    single_plan_b_oop_aarav = round(billed_total_aarav - plan_b_total_pays, 2)
    aarav_savings = round(single_plan_b_oop_aarav - aarav_oop, 2)

    aarav_breakdown = {
        "patient": "Aarav Sen",
        "claim_type": "ACL Reconstruction Surgery (CPT 29888 + 29881)",
        "total_billed": billed_total_aarav,
        "primary_plan": {
            "plan": "Plan B (Insurer2 — PremiumShield Platinum)",
            "role": "PRIMARY",
            "allowed_amount": total_allowed_b,
            "deductible": plan_b_deductible_aarav,
            "deductible_already_met": plan_b_deductible_met_aarav,
            "deductible_applied": plan_b_deductible_applied,
            "after_deductible": after_deductible_b,
            "coinsurance_rate": f"{int(ben_b['coinsurance_plan_pays']*100)}/{int(ben_b['coinsurance_member_pays']*100)}",
            "plan_pays": plan_b_total_pays,
            "member_deductible_oop": plan_b_deductible_applied,
            "member_coinsurance_oop": plan_b_member_coinsurance,
            "member_total_oop_this_plan": plan_b_member_oop_primary,
        },
        "secondary_plan": {
            "plan": "Plan A (Insurer1 — CorporateCare Gold)",
            "role": "SECONDARY",
            "allowed_amount": total_allowed_a,
            "deductible": plan_a_deductible_aarav,
            "deductible_already_met": plan_a_deductible_met_aarav,
            "deductible_applied": plan_a_deductible_applied_secondary,
            "hypothetical_primary_payment": plan_a_hypothetical_primary_pay,
            "remaining_after_primary": remaining_after_primary,
            "plan_pays": plan_a_secondary_pays,
            "cob_method": "Non-Duplication (lesser of hypothetical primary or remaining balance)",
        },
        "summary": {
            "total_insurance_pays": round(plan_b_total_pays + plan_a_secondary_pays, 2),
            "plan_b_pays": plan_b_total_pays,
            "plan_a_pays": plan_a_secondary_pays,
            "patient_oop": aarav_oop,
            "single_plan_oop_if_no_secondary": single_plan_b_oop_aarav,
            "savings_from_dual_coverage": aarav_savings,
        }
    }

    print("  [CALC] Calculating Priya's PT costs (Primary: Plan A, Secondary: Plan B)...")

    billed_total_priya = parsed.get("pt_invoice", {}).get("total_amount", 30000)

    allowed_97161_a = PLAN_A_ALLOWED["97161"]    # ₹3,500
    allowed_97110_a_per = PLAN_A_ALLOWED["97110"] # ₹3,000 per session
    allowed_97110_a = allowed_97110_a_per * 5     # 5 sessions = ₹15,000
    total_allowed_priya_a = allowed_97161_a + allowed_97110_a  # ₹18,500

    plan_a_deductible_priya = ben_a["annual_deductible_individual"]
    plan_a_deductible_met_priya = ben_a.get("deductible_met_priya", 8000)  # ₹8,000 already met
    plan_a_deductible_remaining_priya = max(0, plan_a_deductible_priya - plan_a_deductible_met_priya)

    plan_a_deductible_applied_priya = min(plan_a_deductible_remaining_priya, total_allowed_priya_a)
    after_deductible_a_priya = total_allowed_priya_a - plan_a_deductible_applied_priya
    plan_a_pays_priya = round(after_deductible_a_priya * ben_a["coinsurance_plan_pays"], 2)
    plan_a_member_priya = plan_a_deductible_applied_priya + round(after_deductible_a_priya * ben_a["coinsurance_member_pays"], 2)

    plan_b_deductible_priya = ben_b["annual_deductible_individual"]
    plan_b_deductible_met_priya = ben_b.get("deductible_met_priya", 5000)  # ₹5,000 already met
    plan_b_deductible_remaining_priya = max(0, plan_b_deductible_priya - plan_b_deductible_met_priya)

    allowed_97161_b = PLAN_B_ALLOWED["97161"]
    allowed_97110_b = PLAN_B_ALLOWED["97110"] * 5
    total_allowed_priya_b = allowed_97161_b + allowed_97110_b  # ₹19,800

    plan_b_deductible_applied_priya = min(plan_b_deductible_remaining_priya, total_allowed_priya_b)
    after_deductible_b_priya = total_allowed_priya_b - plan_b_deductible_applied_priya
    plan_b_hypothetical_primary_priya = round(after_deductible_b_priya * ben_b["coinsurance_plan_pays"], 2)

    remaining_after_primary_priya = max(0, billed_total_priya - plan_a_pays_priya)
    plan_b_secondary_pays_priya = min(plan_b_hypothetical_primary_priya, remaining_after_primary_priya)
    plan_b_secondary_pays_priya = round(plan_b_secondary_pays_priya, 2)

    priya_oop = max(0, round(billed_total_priya - plan_a_pays_priya - plan_b_secondary_pays_priya, 2))
    single_plan_a_oop_priya = round(billed_total_priya - plan_a_pays_priya, 2)
    priya_savings = round(single_plan_a_oop_priya - priya_oop, 2)

    priya_breakdown = {
        "patient": "Priya Sen",
        "claim_type": "Physical Therapy (CPT 97161 + 97110 x5 sessions)",
        "total_billed": billed_total_priya,
        "primary_plan": {
            "plan": "Plan A (Insurer1 — CorporateCare Gold)",
            "role": "PRIMARY",
            "allowed_amount": total_allowed_priya_a,
            "deductible": plan_a_deductible_priya,
            "deductible_already_met": plan_a_deductible_met_priya,
            "deductible_remaining": plan_a_deductible_remaining_priya,
            "deductible_applied": plan_a_deductible_applied_priya,
            "after_deductible": after_deductible_a_priya,
            "coinsurance_rate": f"{int(ben_a['coinsurance_plan_pays']*100)}/{int(ben_a['coinsurance_member_pays']*100)}",
            "plan_pays": plan_a_pays_priya,
            "member_total_oop_this_plan": plan_a_member_priya,
        },
        "secondary_plan": {
            "plan": "Plan B (Insurer2 — PremiumShield Platinum)",
            "role": "SECONDARY",
            "allowed_amount": total_allowed_priya_b,
            "deductible": plan_b_deductible_priya,
            "deductible_already_met": plan_b_deductible_met_priya,
            "deductible_applied": plan_b_deductible_applied_priya,
            "hypothetical_primary_payment": plan_b_hypothetical_primary_priya,
            "remaining_after_primary": remaining_after_primary_priya,
            "plan_pays": plan_b_secondary_pays_priya,
            "cob_method": "Non-Duplication",
        },
        "summary": {
            "total_insurance_pays": round(plan_a_pays_priya + plan_b_secondary_pays_priya, 2),
            "plan_a_pays": plan_a_pays_priya,
            "plan_b_pays": plan_b_secondary_pays_priya,
            "patient_oop": priya_oop,
            "single_plan_oop_if_no_secondary": single_plan_a_oop_priya,
            "savings_from_dual_coverage": priya_savings,
        }
    }

    total_billed = billed_total_aarav + billed_total_priya
    total_insurance = round(plan_b_total_pays + plan_a_secondary_pays + plan_a_pays_priya + plan_b_secondary_pays_priya, 2)
    total_oop = round(aarav_oop + priya_oop, 2)
    total_savings = round(aarav_savings + priya_savings, 2)

    financial_breakdown = {
        "aarav": aarav_breakdown,
        "priya": priya_breakdown,
        "family_summary": {
            "total_medical_bills": total_billed,
            "total_covered_by_insurance": total_insurance,
            "total_family_oop": total_oop,
            "total_savings_from_dual_coverage": total_savings,
            "plan_a_total_pays": round(plan_a_secondary_pays + plan_a_pays_priya, 2),
            "plan_b_total_pays": round(plan_b_total_pays + plan_b_secondary_pays_priya, 2),
            "coverage_percentage": round((total_insurance / total_billed) * 100, 1) if total_billed > 0 else 0,
        }
    }

    print(f"  [OK] Total billed: INR {total_billed:,.0f}")
    print(f"  [OK] Insurance covers: INR {total_insurance:,.0f} ({financial_breakdown['family_summary']['coverage_percentage']}%)")
    print(f"  [OK] Family OOP: INR {total_oop:,.0f}")
    print(f"  [OK] Savings from dual coverage: INR {total_savings:,.0f}")

    messages.append(f"[OK] Aarav OOP: INR {aarav_oop:,.2f} (saved INR {aarav_savings:,.2f} from dual coverage)")
    messages.append(f"[OK] Priya OOP: INR {priya_oop:,.2f} (saved INR {priya_savings:,.2f} from dual coverage)")
    messages.append(f"[OK] Family total OOP: INR {total_oop:,.2f} on INR {total_billed:,.0f} in bills")

    return {
        "financial_breakdown": financial_breakdown,
        "aarav_oop": aarav_oop,
        "priya_oop": priya_oop,
        "total_oop": total_oop,
        "savings_from_dual_coverage": total_savings,
        "messages": messages,
        "current_step": "financial_calc_complete",
    }
