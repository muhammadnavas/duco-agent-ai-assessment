"""Mock Insurance API — Insurer2 (Plan B)"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Insurer2 Plan B API", version="1.0.0")

PLAN_B_CONFIG = {
    "plan_id": "INSURER2-PLAN-B-2026",
    "insurer": "Insurer2 Assurance Corporation",
    "plan_name": "PremiumShield Platinum Plan",
    "policy_number": "IC2-MUM-2026-ARV-001",
    "group_number": "CORP-GRPB-7734",
    "network": "In-Network",
    "policy_year": "2026",
    "primary_holder": {
        "name": "Aarav Sen",
        "member_id": "IC2-PH-2026-AARAV",
        "dob": "1988-03-15",
        "relationship": "Primary",
        "employer": "GlobalFinance Analytics Ltd.",
    },
    "dependent": {
        "name": "Priya Sen",
        "member_id": "IC2-DEP-2026-PRIYA",
        "dob": "1989-08-22",
        "relationship": "Spouse",
    },
    "benefits": {
        "annual_deductible_individual": 25000,
        "annual_deductible_family": 50000,
        "deductible_met_aarav": 0,
        "deductible_met_priya": 5000,
        "coinsurance_plan_pays": 0.75,
        "coinsurance_member_pays": 0.25,
        "out_of_pocket_max_individual": 250000,
        "out_of_pocket_max_family": 500000,
        "oop_met_aarav": 0,
        "oop_met_priya": 5000,
        "copay_pcp": 750,
        "copay_specialist": 1500,
        "lifetime_maximum": None,
    },
    "coverage": {
        "surgical_procedures": True,
        "physical_therapy": True,
        "pt_visits_per_year": 25,
        "pt_visits_used": 0,
        "diagnostic_imaging": True,
        "prescription_drugs": True,
        "pre_authorization_required": ["29888", "29881", "27447", "22612", "29827"],
        "pre_auth_turnaround_days": 5,
    },
    "cob_coordination": {
        "cob_type": "Standard",
        "coordination_method": "Maintenance-of-Benefits",
        "birthday_rule_applies": True,
    },
}

PLAN_B_ALLOWED_AMOUNTS = {
    "29888": 330000,
    "29881": 92000,
    "97161": 3800,
    "97110": 3200,
}


@app.get("/plan", summary="Get full Plan B configuration")
def get_plan():
    return PLAN_B_CONFIG


@app.get("/benefits", summary="Get Plan B benefits summary")
def get_benefits():
    return PLAN_B_CONFIG["benefits"]


@app.get("/member/{member_id}", summary="Get member details")
def get_member(member_id: str):
    if member_id == PLAN_B_CONFIG["primary_holder"]["member_id"]:
        return PLAN_B_CONFIG["primary_holder"]
    elif member_id == PLAN_B_CONFIG["dependent"]["member_id"]:
        return PLAN_B_CONFIG["dependent"]
    raise HTTPException(status_code=404, detail=f"Member {member_id} not found in Plan B")


@app.get("/preauth/check/{cpt_code}", summary="Check if pre-auth required for CPT code")
def check_preauth(cpt_code: str):
    required = cpt_code in PLAN_B_CONFIG["coverage"]["pre_authorization_required"]
    return {
        "cpt_code": cpt_code,
        "pre_authorization_required": required,
        "turnaround_days": PLAN_B_CONFIG["coverage"]["pre_auth_turnaround_days"] if required else None,
        "plan": "Plan B — Insurer2",
    }


class ClaimRequest(BaseModel):
    member_id: str
    cpt_codes: list[str]
    billed_amount: float
    is_secondary: bool = False
    primary_paid: Optional[float] = None
    primary_deductible_applied: Optional[float] = None


@app.post("/calculate/claim", summary="Calculate Plan B liability for a claim")
def calculate_claim(req: ClaimRequest):
    benefits = PLAN_B_CONFIG["benefits"]
    results = []
    total_plan_pays = 0.0
    total_member_pays = 0.0
    total_not_covered = 0.0

    for cpt in req.cpt_codes:
        allowed = PLAN_B_ALLOWED_AMOUNTS.get(cpt)
        if allowed is None:
            results.append({
                "cpt_code": cpt,
                "status": "NOT_COVERED",
                "plan_pays": 0,
                "member_pays": 0,
            })
            total_not_covered += 1
            continue

        billed_for_cpt = PLAN_B_ALLOWED_AMOUNTS.get(cpt, req.billed_amount)

        if req.is_secondary:
            remaining = max(0, billed_for_cpt - (req.primary_paid or 0))
            if req.member_id == PLAN_B_CONFIG["primary_holder"]["member_id"]:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_aarav"])
            else:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_priya"])

            after_ded = max(0, remaining - ded_remaining)
            plan_pays = round(after_ded * benefits["coinsurance_plan_pays"], 2)
            member_pays = round(remaining - plan_pays, 2)
        else:
            if req.member_id == PLAN_B_CONFIG["primary_holder"]["member_id"]:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_aarav"])
            else:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_priya"])

            after_ded = max(0, billed_for_cpt - ded_remaining)
            plan_pays = round(after_ded * benefits["coinsurance_plan_pays"], 2)
            member_pays = round(billed_for_cpt - plan_pays, 2)

        results.append({
            "cpt_code": cpt,
            "billed_amount": billed_for_cpt,
            "allowed_amount": allowed,
            "status": "COVERED",
            "plan_pays": plan_pays,
            "member_pays": member_pays,
        })
        total_plan_pays += plan_pays
        total_member_pays += member_pays

    return {
        "plan": "Plan B — Insurer2",
        "member_id": req.member_id,
        "is_secondary": req.is_secondary,
        "line_items": results,
        "summary": {
            "total_plan_pays": round(total_plan_pays, 2),
            "total_member_pays": round(total_member_pays, 2),
            "not_covered_codes": total_not_covered,
        },
    }


@app.get("/allowed-amount/{cpt_code}", summary="Get in-network allowed amount for CPT code")
def get_allowed_amount(cpt_code: str):
    amount = PLAN_B_ALLOWED_AMOUNTS.get(cpt_code)
    if amount is None:
        raise HTTPException(status_code=404, detail=f"CPT {cpt_code} not in Plan B fee schedule")
    return {"cpt_code": cpt_code, "allowed_amount": amount, "plan": "Plan B — Insurer2"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
