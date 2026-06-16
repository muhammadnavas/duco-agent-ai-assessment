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


# ── In-network allowed amounts by plan ──────────────────────
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

    # ════════════════════════════════════════════════════════
    # AARAV'S SURGERY — ACL Reconstruction + Meniscectomy
    # Primary: Plan B (Insurer2) | Secondary: Plan A (Insurer1)
    # ════════════════════════════════════════════════════════
    print("  💰 Calculating Aarav's surgery costs (Primary: Plan B, Secondary: Plan A)...")

    # ── Plan B (Primary) — Aarav's deductible: ₹25,000 (none met YTD) ──
    plan_b_deductible_aarav = ben_b["annual_deductible_individual"]
    plan_b_deductible_met_aarav = ben_b.get("deductible_met_aarav", 0)
    plan_b_deductible_remaining = max(0, plan_b_deductible_aarav - plan_b_deductible_met_aarav)

    # Allowed amounts under Plan B
    allowed_29888_b = PLAN_B_ALLOWED["29888"]   # ₹3,30,000
    allowed_29881_b = PLAN_B_ALLOWED["29881"]   # ₹92,000
    total_allowed_b = allowed_29888_b + allowed_29881_b  # ₹4,22,000

    # Apply Plan B deductible
    plan_b_deductible_applied = min(plan_b_deductible_remaining, total_allowed_b)
    after_deductible_b = total_allowed_b - plan_b_deductible_applied

    # Plan B coinsurance (75% plan, 25% member)
    plan_b_pays_coinsurance = round(after_deductible_b * ben_b["coinsurance_plan_pays"], 2)
    plan_b_member_coinsurance = round(after_deductible_b * ben_b["coinsurance_member_pays"], 2)

    # Plan B total obligation
    plan_b_total_pays = plan_b_pays_coinsurance
    plan_b_member_oop_primary = plan_b_deductible_applied + plan_b_member_coinsurance

    # ── Plan A (Secondary) — Aarav's deductible on Plan A ──
    plan_a_deductible_aarav = ben_a["annual_deductible_individual"]
    plan_a_deductible_met_aarav = ben_a.get("deductible_met_aarav", 0)
    plan_a_deductible_remaining = max(0, plan_a_deductible_aarav - plan_a_deductible_met_aarav)

    # Allowed amounts under Plan A
    allowed_29888_a = PLAN_A_ALLOWED["29888"]   # ₹3,20,000
    allowed_29881_a = PLAN_A_ALLOWED["29881"]   # ₹90,000
    total_allowed_a = allowed_29888_a + allowed_29881_a  # ₹4,10,000

    # Secondary calculates on its own allowed amounts minus what primary already paid
    # Non-duplication: secondary won't pay more than it would if it were primary
    primary_paid_plan_b = plan_b_total_pays

    # Secondary (Plan A) applies to whatever balance remains up to Plan A's allowed amount
    # Plan A sees the claim at its contracted rate, credits the primary payment
    plan_a_secondary_allowed = total_allowed_a  # Plan A's view of total allowed

    # Apply Plan A secondary deductible
    plan_a_deductible_applied_secondary = min(plan_a_deductible_remaining, plan_a_secondary_allowed)
    after_deductible_a_secondary = plan_a_secondary_allowed - plan_a_deductible_applied_secondary

    # Plan A would pay (if primary): 80% of after-deductible
    plan_a_hypothetical_primary_pay = round(after_deductible_a_secondary * ben_a["coinsurance_plan_pays"], 2)

    # Secondary credit: Plan A pays the LESSER of:
    #   (a) what it would pay as primary, OR
    #   (b) actual remaining balance after Plan B paid
    billed_total_aarav = parsed.get("surgeon_estimate", {}).get("total_estimated_charge", 450000)
    remaining_after_primary = max(0, billed_total_aarav - plan_b_total_pays)

    plan_a_secondary_pays = min(plan_a_hypothetical_primary_pay, remaining_after_primary)
    plan_a_secondary_pays = round(plan_a_secondary_pays, 2)

    # Aarav's final OOP
    aarav_oop = round(billed_total_aarav - plan_b_total_pays - plan_a_secondary_pays, 2)
    aarav_oop = max(0, aarav_oop)

    # Single-plan OOP (if only Plan B) for savings calculation
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

    # ════════════════════════════════════════════════════════
    # PRIYA'S PT BILLS — Physical Therapy
    # Primary: Plan A (Insurer1) | Secondary: Plan B (Insurer2)
    # ════════════════════════════════════════════════════════
    print("  💰 Calculating Priya's PT costs (Primary: Plan A, Secondary: Plan B)...")

    billed_total_priya = parsed.get("pt_invoice", {}).get("total_amount", 30000)

    # Priya's PT breakdown: 1x Eval (97161 @ ₹5,000) + 5x Exercise (97110 @ ₹5,000 each)
    # Plan A allowed rates:
    allowed_97161_a = PLAN_A_ALLOWED["97161"]    # ₹3,500
    allowed_97110_a_per = PLAN_A_ALLOWED["97110"] # ₹3,000 per session
    allowed_97110_a = allowed_97110_a_per * 5     # 5 sessions = ₹15,000
    total_allowed_priya_a = allowed_97161_a + allowed_97110_a  # ₹18,500

    # Plan A — Primary for Priya
    plan_a_deductible_priya = ben_a["annual_deductible_individual"]
    plan_a_deductible_met_priya = ben_a.get("deductible_met_priya", 8000)  # ₹8,000 already met
    plan_a_deductible_remaining_priya = max(0, plan_a_deductible_priya - plan_a_deductible_met_priya)

    plan_a_deductible_applied_priya = min(plan_a_deductible_remaining_priya, total_allowed_priya_a)
    after_deductible_a_priya = total_allowed_priya_a - plan_a_deductible_applied_priya
    plan_a_pays_priya = round(after_deductible_a_priya * ben_a["coinsurance_plan_pays"], 2)
    plan_a_member_priya = plan_a_deductible_applied_priya + round(after_deductible_a_priya * ben_a["coinsurance_member_pays"], 2)

    # Plan B — Secondary for Priya
    plan_b_deductible_priya = ben_b["annual_deductible_individual"]
    plan_b_deductible_met_priya = ben_b.get("deductible_met_priya", 5000)  # ₹5,000 already met
    plan_b_deductible_remaining_priya = max(0, plan_b_deductible_priya - plan_b_deductible_met_priya)

    # Plan B allowed rates
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

    # ════════════════════════════════════════════════════════
    # COMBINED FAMILY SUMMARY
    # ════════════════════════════════════════════════════════
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

    print(f"  ✅ Total billed: ₹{total_billed:,.0f}")
    print(f"  ✅ Insurance covers: ₹{total_insurance:,.0f} ({financial_breakdown['family_summary']['coverage_percentage']}%)")
    print(f"  ✅ Family OOP: ₹{total_oop:,.0f}")
    print(f"  ✅ Savings from dual coverage: ₹{total_savings:,.0f}")

    messages.append(f"✅ Aarav OOP: ₹{aarav_oop:,.2f} (saved ₹{aarav_savings:,.2f} from dual coverage)")
    messages.append(f"✅ Priya OOP: ₹{priya_oop:,.2f} (saved ₹{priya_savings:,.2f} from dual coverage)")
    messages.append(f"✅ Family total OOP: ₹{total_oop:,.2f} on ₹{total_billed:,.0f} in bills")

    return {
        "financial_breakdown": financial_breakdown,
        "aarav_oop": aarav_oop,
        "priya_oop": priya_oop,
        "total_oop": total_oop,
        "savings_from_dual_coverage": total_savings,
        "messages": messages,
        "current_step": "financial_calc_complete",
    }
