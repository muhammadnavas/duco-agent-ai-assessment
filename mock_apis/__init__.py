# DuCO-Agent Package — Mock APIs
from mock_apis.insurer1_plan_a import (
    get_plan as plan_a_get_plan,
    get_benefits as plan_a_get_benefits,
    get_member as plan_a_get_member,
    check_preauth as plan_a_check_preauth,
    calculate_claim as plan_a_calculate_claim,
    get_allowed_amount as plan_a_get_allowed_amount,
    ClaimRequest as PlanAClaimRequest,
)
from mock_apis.insurer2_plan_b import (
    get_plan as plan_b_get_plan,
    get_benefits as plan_b_get_benefits,
    get_member as plan_b_get_member,
    check_preauth as plan_b_check_preauth,
    calculate_claim as plan_b_calculate_claim,
    get_allowed_amount as plan_b_get_allowed_amount,
    ClaimRequest as PlanBClaimRequest,
)

__all__ = [
    # Plan A (Insurer1)
    "plan_a_get_plan",
    "plan_a_get_benefits",
    "plan_a_get_member",
    "plan_a_check_preauth",
    "plan_a_calculate_claim",
    "plan_a_get_allowed_amount",
    "PlanAClaimRequest",
    # Plan B (Insurer2)
    "plan_b_get_plan",
    "plan_b_get_benefits",
    "plan_b_get_member",
    "plan_b_check_preauth",
    "plan_b_calculate_claim",
    "plan_b_get_allowed_amount",
    "PlanBClaimRequest",
]
