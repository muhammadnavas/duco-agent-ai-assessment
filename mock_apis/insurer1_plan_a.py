"""Mock Insurance API — Insurer1 (Plan A)"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Insurer1 Plan A API", version="1.0.0")

PLAN_A_CONFIG = {
    "plan_id": "INSURER1-PLAN-A-2026",
    "insurer": "Insurer1 Health Insurance Ltd.",
    "plan_name": "CorporateCare Gold Plan",
    "policy_number": "IC1-MUM-2026-PRY-001",
    "group_number": "CORP-GRPA-5521",
    "network": "In-Network",
    "policy_year": "2026",
    "primary_holder": {
        "name": "Priya Sen",
        "member_id": "IC1-PH-2026-PRIYA",
        "dob": "1989-08-22",
        "relationship": "Primary",
        "employer": "TechSolutions Pvt. Ltd.",
    },
    "dependent": {
        "name": "Aarav Sen",
        "member_id": "IC1-DEP-2026-AARAV",
        "dob": "1988-03-15",
        "relationship": "Spouse",
    },
    "benefits": {
        "annual_deductible_individual": 20000,
        "annual_deductible_family": 40000,
        "deductible_met_priya": 8000,
        "deductible_met_aarav": 0,
        "coinsurance_plan_pays": 0.80,
        "coinsurance_member_pays": 0.20,
        "out_of_pocket_max_individual": 200000,
        "out_of_pocket_max_family": 400000,
        "oop_met_priya": 8000,
        "oop_met_aarav": 0,
        "copay_pcp": 500,
        "copay_specialist": 1000,
        "lifetime_maximum": None,
    },
    "coverage": {
        "surgical_procedures": True,
        "physical_therapy": True,
        "pt_visits_per_year": 30,
        "pt_visits_used": 5,
        "diagnostic_imaging": True,
        "prescription_drugs": True,
        "pre_authorization_required": ["29888", "29881", "27447", "22612"],
        "pre_auth_turnaround_days": 3,
    },
    "cob_coordination": {
        "cob_type": "Standard",
        "coordination_method": "Non-Duplication",
        "birthday_rule_applies": True,
    },
}

PLAN_A_ALLOWED_AMOUNTS = {
    "29888": 320000,
    "29881": 90000,
    "97161": 3500,
    "97110": 3000,
}


@app.get("/plan", summary="Get full Plan A configuration")
def get_plan():
    return PLAN_A_CONFIG


@app.get("/benefits", summary="Get Plan A benefits summary")
def get_benefits():
    return PLAN_A_CONFIG["benefits"]


@app.get("/member/{member_id}", summary="Get member details")
def get_member(member_id: str):
    if member_id == PLAN_A_CONFIG["primary_holder"]["member_id"]:
        return PLAN_A_CONFIG["primary_holder"]
    elif member_id == PLAN_A_CONFIG["dependent"]["member_id"]:
        return PLAN_A_CONFIG["dependent"]
    raise HTTPException(status_code=404, detail=f"Member {member_id} not found in Plan A")


@app.get("/preauth/check/{cpt_code}", summary="Check if pre-auth required for CPT code")
def check_preauth(cpt_code: str):
    required = cpt_code in PLAN_A_CONFIG["coverage"]["pre_authorization_required"]
    return {
        "cpt_code": cpt_code,
        "pre_authorization_required": required,
        "turnaround_days": PLAN_A_CONFIG["coverage"]["pre_auth_turnaround_days"] if required else None,
        "plan": "Plan A — Insurer1",
    }


class ClaimRequest(BaseModel):
    member_id: str
    cpt_codes: list[str]
    billed_amount: float
    is_secondary: bool = False
    primary_paid: Optional[float] = None
    primary_deductible_applied: Optional[float] = None


@app.post("/calculate/claim", summary="Calculate Plan A liability for a claim")
def calculate_claim(req: ClaimRequest):
    benefits = PLAN_A_CONFIG["benefits"]
    results = []
    total_plan_pays = 0.0
    total_member_pays = 0.0
    total_not_covered = 0.0

    for cpt in req.cpt_codes:
        allowed = PLAN_A_ALLOWED_AMOUNTS.get(cpt)
        if allowed is None:
            results.append({
                "cpt_code": cpt,
                "status": "NOT_COVERED",
                "plan_pays": 0,
                "member_pays": 0,
            })
            total_not_covered += 1
            continue

        billed_for_cpt = PLAN_A_ALLOWED_AMOUNTS.get(cpt, req.billed_amount)

        if req.is_secondary:
            remaining = max(0, billed_for_cpt - (req.primary_paid or 0))
            if req.member_id == PLAN_A_CONFIG["primary_holder"]["member_id"]:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_priya"])
            else:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_aarav"])

            after_ded = max(0, remaining - ded_remaining)
            plan_pays = round(after_ded * benefits["coinsurance_plan_pays"], 2)
            member_pays = round(remaining - plan_pays, 2)
        else:
            if req.member_id == PLAN_A_CONFIG["primary_holder"]["member_id"]:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_priya"])
            else:
                ded_remaining = max(0, benefits["annual_deductible_individual"] - benefits["deductible_met_aarav"])

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
        "plan": "Plan A — Insurer1",
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
    amount = PLAN_A_ALLOWED_AMOUNTS.get(cpt_code)
    if amount is None:
        raise HTTPException(status_code=404, detail=f"CPT {cpt_code} not in Plan A fee schedule")
    return {"cpt_code": cpt_code, "allowed_amount": amount, "plan": "Plan A — Insurer1"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
