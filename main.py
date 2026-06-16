"""
main.py
--------
DuCO-Agent Main Entry Point
Orchestrates the full LangGraph pipeline for Coordination of Benefits processing.

Usage:
    python main.py
    python main.py --setup   (generates mock input files first)
    python main.py --graph   (shows LangGraph structure and exits)
"""
import os
import sys
import json
import argparse
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.markdown import Markdown
from rich import box
from dotenv import load_dotenv

load_dotenv()

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold blue]DuCO-Agent[/bold blue] - [cyan]Dual Coverage Optimization[/cyan]\n"
        "[dim]Agentic Multi-Modal AI System | LangGraph Pipeline[/dim]\n"
        "[yellow]Prudential Health India Assessment 2026[/yellow]",
        border_style="blue",
        padding=(1, 4),
    ))


def setup_mock_inputs():
    """Generate mock input files if they don't exist."""
    inputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_inputs")
    pdf_path = os.path.join(inputs_dir, "aarav_mri_report.pdf")

    if not os.path.exists(pdf_path):
        console.print("[yellow]Generating mock MRI PDF report...[/yellow]")
        try:
            sys.path.insert(0, inputs_dir)
            from generate_mri_pdf import generate_mri_report
            generate_mri_report()
            console.print("[green]OK MRI PDF generated successfully[/green]")
        except Exception as e:
            console.print(f"[red]ERROR MRI PDF generation failed: {e}[/red]")
    else:
        console.print("[dim]OK MRI PDF already exists[/dim]")


def check_env():
    """Validate environment setup."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print(Panel(
            "[bold red]ERROR GOOGLE_API_KEY not set![/bold red]\n\n"
            "Please create a [yellow].env[/yellow] file with:\n"
            "[cyan]GOOGLE_API_KEY=your_key_here[/cyan]\n\n"
            "See [dim].env.example[/dim] for reference.",
            title="Configuration Error",
            border_style="red"
        ))
        sys.exit(1)
    console.print(f"[green]OK Google API Key found[/green] [dim](***{api_key[-4:]})[/dim]")


def run_pipeline():
    """Execute the full DuCO-Agent LangGraph pipeline."""
    from graph.duco_graph import compile_graph

    # ── Initial State ──────────────────────────────────────────
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_dir = os.path.join(base_dir, "mock_inputs")

    initial_state = {
        "raw_inputs": {
            "base_dir": base_dir,
            "pt_invoice": os.path.join(inputs_dir, "priya_pt_invoice.png"),
            "mri_report": os.path.join(inputs_dir, "aarav_mri_report.pdf"),
            "surgeon_estimate": os.path.join(inputs_dir, "surgeon_estimate.jpg"),
            "user_query": os.path.join(inputs_dir, "user_query.txt"),
        },
        "parsed_documents": {},
        "cpt_codes": [],
        "icd10_codes": [],
        "code_lookup_complete": False,
        "code_validation_errors": [],
        "plan_a_data": {},
        "plan_b_data": {},
        "cob_aarav": {},
        "cob_priya": {},
        "cob_reasoning": "",
        "preauth_required": {},
        "preauth_status": "unknown",
        "financial_breakdown": {},
        "aarav_oop": 0.0,
        "priya_oop": 0.0,
        "total_oop": 0.0,
        "savings_from_dual_coverage": 0.0,
        "preauth_letters": {},
        "cost_flow_html": "",
        "audio_brief_text": "",
        "audio_brief_path": "",
        "final_report_html": "",
        "messages": ["🚀 DuCO-Agent pipeline starting..."],
        "current_step": "init",
        "validation_errors": [],
        "retry_count": 0,
        "is_complete": False,
    }

    console.print("\n[bold]Compiling LangGraph...[/bold]")
    graph = compile_graph()
    console.print("[green]OK Graph compiled[/green]\n")

    # ── Execute ────────────────────────────────────────────────
    console.rule("[bold blue]Pipeline Execution[/bold blue]")
    start_time = time.time()

    config = {"configurable": {"thread_id": "duco-sen-family-001"}}

    final_state = None
    for chunk in graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = chunk
        step = chunk.get("current_step", "")
        if step and step != "init":
            console.print(f"  [dim]Step:[/dim] [cyan]{step}[/cyan]")

    elapsed = time.time() - start_time
    console.print(f"\n[green]OK Pipeline complete in {elapsed:.1f}s[/green]\n")

    return final_state


def print_results(state: dict):
    """Print a rich summary of results to the console."""
    console.rule("[bold green]DuCO-Agent Results[/bold green]")

    financial = state.get("financial_breakdown", {})
    family = financial.get("family_summary", {})

    # -- Financial Summary Table --------------------------------
    table = Table(title="Financial Summary - Sen Family", box=box.ROUNDED,
                  border_style="blue", show_header=True, header_style="bold cyan")
    table.add_column("Category", style="dim", width=35)
    table.add_column("Amount (INR)", justify="right", style="bold")

    table.add_row("Total Medical Bills", f"INR {family.get('total_medical_bills', 0):,.2f}")
    table.add_row("Insurance Covers (Both Plans)", f"INR {family.get('total_covered_by_insurance', 0):,.2f}",)
    table.add_row("Plan B (Insurer2) Total Pays", f"INR {family.get('plan_b_total_pays', 0):,.2f}")
    table.add_row("Plan A (Insurer1) Total Pays", f"INR {family.get('plan_a_total_pays', 0):,.2f}")
    table.add_row("", "")  # spacer
    table.add_row("[bold red]Family Out-of-Pocket (OOP)", f"[bold red]INR {family.get('total_family_oop', 0):,.2f}")
    table.add_row("[green]Savings from Dual Coverage", f"[green]INR {family.get('total_savings_from_dual_coverage', 0):,.2f}")
    table.add_row("Coverage Percentage", f"{family.get('coverage_percentage', 0):.1f}%")

    console.print(table)

    console.print("\n[bold cyan]COB Determination[/bold cyan]")
    console.print(f"  Aarav's Surgery: [green]Primary -> Plan B (Insurer2)[/green] | [blue]Secondary -> Plan A (Insurer1)[/blue]")
    console.print(f"  Priya's PT:      [blue]Primary -> Plan A (Insurer1)[/blue] | [green]Secondary -> Plan B (Insurer2)[/green]")

    # ── Outputs ───────────────────────────────────────────────
    console.print("\n[bold cyan]Generated Outputs[/bold cyan]")
    outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    for fname in ["duco_report.html", "preauth_letter_plan_a.pdf", "preauth_letter_plan_b.pdf", "audio_brief.mp3", "audio_brief_script.txt"]:
        fpath = os.path.join(outputs_dir, fname)
        if os.path.exists(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            console.print(f"  [green]OK[/green] {fname} [dim]({size_kb:.1f} KB)[/dim]")
        else:
            console.print(f"  [yellow]WARN[/yellow]  {fname} [dim](not generated)[/dim]")

    # ── Messages ──────────────────────────────────────────────
    console.print("\n[bold cyan]Agent Messages[/bold cyan]")
    for msg in state.get("messages", [])[-10:]:  # Last 10
        console.print(f"  {msg}")

    console.print("\n[bold green]DuCO-Agent completed successfully![/bold green]")
    console.print(f"[dim]Open [cyan]outputs/duco_report.html[/cyan] in your browser for the full report.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="DuCO-Agent — Dual Coverage Optimization")
    parser.add_argument("--setup", action="store_true", help="Generate mock input files and exit")
    parser.add_argument("--graph", action="store_true", help="Show graph structure and exit")
    parser.add_argument("--skip-setup", action="store_true", help="Skip mock file generation")
    args = parser.parse_args()

    print_banner()

    if args.graph:
        from graph.duco_graph import print_graph_structure
        print_graph_structure()
        return

    check_env()

    if not args.skip_setup:
        console.print("\n[bold]Setting up mock inputs...[/bold]")
        setup_mock_inputs()

    if args.setup:
        console.print("[green]Setup complete.[/green]")
        return

    # Run the full pipeline
    final_state = run_pipeline()

    if final_state:
        print_results(final_state)
    else:
        console.print("[red]ERROR Pipeline failed — no final state returned[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
