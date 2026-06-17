import pytest
from agents.financial_calc_agent import run_financial_calc_agent

def get_mock_state():
    return {
        "plan_a_data": {
            "benefits": {
                "annual_deductible_individual": 20000,
                "deductible_met_aarav": 0,
                "deductible_met_priya": 8000,
                "coinsurance_plan_pays": 0.80,
                "coinsurance_member_pays": 0.20
            }
        },
        "plan_b_data": {
            "benefits": {
                "annual_deductible_individual": 25000,
                "deductible_met_aarav": 0,
                "deductible_met_priya": 5000,
                "coinsurance_plan_pays": 0.75,
                "coinsurance_member_pays": 0.25
            }
        },
        "parsed_documents": {
            "surgeon_estimate": {
                "total_estimated_charge": 450000
            },
            "pt_invoice": {
                "total_amount": 30000
            }
        }
    }

def test_aarav_surgery_financials():
    """Test Aarav's COB financials (Plan B Primary, Plan A Secondary)."""
    state = get_mock_state()
    result = run_financial_calc_agent(state)
    
    aarav = result["financial_breakdown"]["aarav"]
    
    # Assert primary plan logic (Plan B)
    assert aarav["primary_plan"]["role"] == "PRIMARY"
    assert aarav["primary_plan"]["deductible_applied"] == 25000
    
    # Assert secondary plan logic (Plan A)
    assert aarav["secondary_plan"]["role"] == "SECONDARY"
    assert aarav["secondary_plan"]["cob_method"] == "Non-Duplication (lesser of hypothetical primary or remaining balance)"
    
    # Assert final OOP
    # Aarav OOP should be 0 because the secondary plan covers the remaining patient balance
    assert aarav["summary"]["patient_oop"] == 0

def test_priya_pt_financials():
    """Test Priya's COB financials (Plan A Primary, Plan B Secondary)."""
    state = get_mock_state()
    result = run_financial_calc_agent(state)
    
    priya = result["financial_breakdown"]["priya"]
    
    # Assert primary plan logic (Plan A)
    assert priya["primary_plan"]["role"] == "PRIMARY"
    
    # Priya has an 8000 deductible met out of 20000, leaving 12000.
    # The total allowed for PT is 3500 + (3000*5) = 18500
    assert priya["primary_plan"]["deductible_applied"] == 12000
    
    # Check total out of pocket calculation
    # Without going deep into the math assertions, we expect the total OOP calculated to match our known correct value.
    assert priya["summary"]["patient_oop"] == 24800

def test_family_totals():
    """Test the family total out of pocket aggregation."""
    state = get_mock_state()
    result = run_financial_calc_agent(state)
    
    totals = result["financial_breakdown"]["family_summary"]
    
    assert totals["total_medical_bills"] == 480000
    assert totals["total_family_oop"] == 24800
    assert totals["total_covered_by_insurance"] == 455200
