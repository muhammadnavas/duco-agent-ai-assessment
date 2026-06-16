"""
graph/duco_graph.py
-------------------
DuCO-Agent LangGraph State Machine
-----------------------------------
Full agentic pipeline for Coordination of Benefits (COB) processing.
Uses LangGraph with typed state, conditional routing, and reflection loops.
"""
from __future__ import annotations
import os
import sys
from typing import TypedDict, Annotated, Optional, Any
import operator

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.intake_agent import run_intake_agent
from agents.code_lookup_agent import run_code_lookup_agent
from agents.preauth_check_agent import run_preauth_check_agent
from agents.cob_logic_agent import run_cob_logic_agent
from agents.financial_calc_agent import run_financial_calc_agent
from agents.letter_gen_agent import run_letter_gen_agent
from agents.visual_output_agent import run_visual_output_agent
from agents.audio_brief_agent import run_audio_brief_agent


# ────────────────────────────────────────────────────────────
# Agent State Definition (TypedDict)
# ────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    # ── Inputs ──
    raw_inputs: dict                   # File paths to all 4 inputs
    parsed_documents: dict             # Structured output from parsers

    # ── Clinical Codes ──
    cpt_codes: list[dict]              # Extracted/inferred CPT codes with details
    icd10_codes: list[dict]            # Extracted/inferred ICD-10 codes
    code_lookup_complete: bool
    code_validation_errors: list[str]

    # ── Insurance Plan Data ──
    plan_a_data: dict                  # Insurer1 Plan A configuration
    plan_b_data: dict                  # Insurer2 Plan B configuration

    # ── COB Determination ──
    cob_aarav: dict                    # COB result for Aarav's surgery
    cob_priya: dict                    # COB result for Priya's PT
    cob_reasoning: str                 # LLM explanation of COB logic

    # ── Pre-Authorization ──
    preauth_required: dict             # {cpt_code: {plan_a: bool, plan_b: bool}}
    preauth_status: str                # "required" / "not_required" / "partial"

    # ── Financial Calculations ──
    financial_breakdown: dict          # Full itemized breakdown
    aarav_oop: float                   # Aarav out-of-pocket total
    priya_oop: float                   # Priya out-of-pocket total
    total_oop: float                   # Combined OOP
    savings_from_dual_coverage: float  # OOP saved vs single-plan coverage

    # ── Generated Outputs ──
    preauth_letters: dict              # {plan_a: path, plan_b: path}
    cost_flow_html: str                # HTML cost flow visualization
    audio_brief_text: str              # Patient-friendly audio script
    audio_brief_path: str              # Path to generated audio file
    final_report_html: str             # Combined HTML report

    # ── Control Flow ──
    messages: Annotated[list, operator.add]   # Conversation log
    current_step: str
    validation_errors: list[str]
    retry_count: int
    is_complete: bool


# ────────────────────────────────────────────────────────────
# Node Wrappers
# ────────────────────────────────────────────────────────────

def intake_node(state: AgentState) -> AgentState:
    """Ingest and parse all 4 multi-modal inputs."""
    print("\n🔵 [DuCO-Agent] ── STEP 1: Intake Agent ──────────────────")
    updates = run_intake_agent(state)
    return {**state, **updates}


def code_lookup_node(state: AgentState) -> AgentState:
    """Look up / infer CPT and ICD-10 codes from clinical descriptions."""
    print("\n🔵 [DuCO-Agent] ── STEP 2: Code Lookup Agent ─────────────")
    updates = run_code_lookup_agent(state)
    return {**state, **updates}


def preauth_check_node(state: AgentState) -> AgentState:
    """Determine pre-authorization requirements for each CPT code and plan."""
    print("\n🔵 [DuCO-Agent] ── STEP 3: Pre-Auth Check Agent ──────────")
    updates = run_preauth_check_agent(state)
    return {**state, **updates}


def cob_logic_node(state: AgentState) -> AgentState:
    """Apply Coordination of Benefits rules to determine primary/secondary payer."""
    print("\n🔵 [DuCO-Agent] ── STEP 4: COB Logic Agent ────────────────")
    updates = run_cob_logic_agent(state)
    return {**state, **updates}


def financial_calc_node(state: AgentState) -> AgentState:
    """Calculate precise financial liability for each plan and patient."""
    print("\n🔵 [DuCO-Agent] ── STEP 5: Financial Calculation Agent ───")
    updates = run_financial_calc_agent(state)
    return {**state, **updates}


def letter_gen_node(state: AgentState) -> AgentState:
    """Generate clinically sound pre-authorization letters for both plans."""
    print("\n🔵 [DuCO-Agent] ── STEP 6: Letter Generation Agent ───────")
    updates = run_letter_gen_agent(state)
    return {**state, **updates}


def visual_output_node(state: AgentState) -> AgentState:
    """Generate visual cost flow chart and HTML report."""
    print("\n🔵 [DuCO-Agent] ── STEP 7: Visual Output Agent ────────────")
    updates = run_visual_output_agent(state)
    return {**state, **updates}


def audio_brief_node(state: AgentState) -> AgentState:
    """Generate patient-friendly audio briefing."""
    print("\n🔵 [DuCO-Agent] ── STEP 8: Audio Brief Agent ─────────────")
    updates = run_audio_brief_agent(state)
    return {**state, **updates}


# ────────────────────────────────────────────────────────────
# Conditional Routing Functions
# ────────────────────────────────────────────────────────────

def should_retry_code_lookup(state: AgentState) -> str:
    """
    After code lookup, check if we have sufficient codes.
    If validation errors and retry count < 2, loop back.
    """
    errors = state.get("code_validation_errors", [])
    retry_count = state.get("retry_count", 0)

    if errors and retry_count < 2:
        print(f"\n⚠️  Code validation errors detected (retry {retry_count + 1}/2): {errors}")
        return "retry_code_lookup"
    elif errors:
        print(f"\n⚠️  Proceeding with warnings after {retry_count} retries.")
        return "proceed_with_warnings"
    else:
        print(f"\n✅ Code lookup validated successfully.")
        return "proceed"


def preauth_routing(state: AgentState) -> str:
    """Route based on whether pre-authorization is required."""
    status = state.get("preauth_status", "not_required")
    if status in ("required", "partial"):
        return "letter_required"
    return "no_letter_required"


# ────────────────────────────────────────────────────────────
# Build LangGraph
# ────────────────────────────────────────────────────────────

def build_duco_graph() -> StateGraph:
    """Construct and compile the DuCO-Agent LangGraph."""

    workflow = StateGraph(AgentState)

    # ── Register Nodes ──
    workflow.add_node("intake", intake_node)
    workflow.add_node("code_lookup", code_lookup_node)
    workflow.add_node("preauth_check", preauth_check_node)
    workflow.add_node("cob_logic", cob_logic_node)
    workflow.add_node("financial_calc", financial_calc_node)
    workflow.add_node("letter_gen", letter_gen_node)
    workflow.add_node("visual_output", visual_output_node)
    workflow.add_node("audio_brief", audio_brief_node)

    # ── Entry Point ──
    workflow.add_edge(START, "intake")

    # ── intake → code_lookup ──
    workflow.add_edge("intake", "code_lookup")

    # ── code_lookup → conditional routing ──
    workflow.add_conditional_edges(
        "code_lookup",
        should_retry_code_lookup,
        {
            "retry_code_lookup": "code_lookup",        # Reflection loop
            "proceed_with_warnings": "preauth_check",
            "proceed": "preauth_check",
        }
    )

    # ── preauth_check → cob_logic (always, preauth info feeds COB) ──
    workflow.add_edge("preauth_check", "cob_logic")

    # ── cob_logic → financial_calc ──
    workflow.add_edge("cob_logic", "financial_calc")

    # ── financial_calc → letter_gen (conditional on preauth requirement) ──
    workflow.add_conditional_edges(
        "financial_calc",
        preauth_routing,
        {
            "letter_required": "letter_gen",
            "no_letter_required": "visual_output",    # Skip letters if not needed
        }
    )

    # ── letter_gen → visual_output ──
    workflow.add_edge("letter_gen", "visual_output")

    # ── visual_output → audio_brief ──
    workflow.add_edge("visual_output", "audio_brief")

    # ── audio_brief → END ──
    workflow.add_edge("audio_brief", END)

    return workflow


def compile_graph():
    """Compile the graph with in-memory checkpointing."""
    memory = MemorySaver()
    workflow = build_duco_graph()
    return workflow.compile(checkpointer=memory)


# ────────────────────────────────────────────────────────────
# Graph Visualization Helper
# ────────────────────────────────────────────────────────────
def print_graph_structure():
    """Print the graph structure for debugging."""
    workflow = build_duco_graph()
    graph = workflow.compile()
    print("\n" + "="*60)
    print("DuCO-Agent LangGraph Structure")
    print("="*60)
    try:
        print(graph.get_graph().draw_ascii())
    except Exception:
        print("Nodes: intake → code_lookup → preauth_check → cob_logic → financial_calc → letter_gen → visual_output → audio_brief → END")


if __name__ == "__main__":
    print_graph_structure()
