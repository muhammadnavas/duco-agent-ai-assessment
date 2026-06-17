"""Visual Output Agent for generating Sankey diagrams and HTML reports."""
import os
import sys
import json
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import plotly.graph_objects as go
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("  [WARN]  Plotly not available — using fallback HTML visualization")


def run_visual_output_agent(state: dict) -> dict:
    """Generates the Sankey cost diagram and HTML report."""
    financial = state.get("financial_breakdown", {})
    cob_aarav = state.get("cob_aarav", {})
    cob_priya = state.get("cob_priya", {})
    cob_reasoning = state.get("cob_reasoning", "")
    preauth = state.get("preauth_required", {})
    preauth_letters = state.get("preauth_letters", {})
    plan_a = state.get("plan_a_data", {})
    plan_b = state.get("plan_b_data", {})
    messages = []

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    family = financial.get("family_summary", {})
    aarav_data = financial.get("aarav", {})
    priya_data = financial.get("priya", {})
    aarav_summary = aarav_data.get("summary", {})
    priya_summary = priya_data.get("summary", {})

    total_billed = family.get("total_medical_bills", 480000)
    total_insurance = family.get("total_covered_by_insurance", 0)
    total_oop = family.get("total_family_oop", 0)
    plan_a_total = family.get("plan_a_total_pays", 0)
    plan_b_total = family.get("plan_b_total_pays", 0)

    aarav_billed = aarav_data.get("total_billed", 450000)
    priya_billed = priya_data.get("total_billed", 30000)
    aarav_plan_b = aarav_summary.get("plan_b_pays", 0)
    aarav_plan_a = aarav_summary.get("plan_a_pays", 0)
    aarav_oop = aarav_summary.get("patient_oop", 0)
    priya_plan_a = priya_summary.get("plan_a_pays", 0)
    priya_plan_b = priya_summary.get("plan_b_pays", 0)
    priya_oop = priya_summary.get("patient_oop", 0)

    cost_flow_html = ""
    if PLOTLY_AVAILABLE:
        cost_flow_html = _generate_sankey(
            aarav_billed, priya_billed,
            aarav_plan_b, aarav_plan_a, aarav_oop,
            priya_plan_a, priya_plan_b, priya_oop
        )
        messages.append("[OK] Sankey cost flow diagram generated")
    else:
        cost_flow_html = "<p><em>Plotly not available — install with: pip install plotly kaleido</em></p>"
        messages.append("[WARN]  Sankey diagram skipped (plotly not installed)")

    html_path = os.path.join(output_dir, "duco_report.html")
    html_content = _generate_html_report(
        financial=financial,
        cob_aarav=cob_aarav,
        cob_priya=cob_priya,
        cob_reasoning=cob_reasoning,
        preauth=preauth,
        preauth_letters=preauth_letters,
        plan_a=plan_a,
        plan_b=plan_b,
        cost_flow_html=cost_flow_html,
        today=date.today().strftime("%d %B %Y"),
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  [OK] HTML report saved: {html_path}")
    messages.append(f"[OK] HTML report generated: {html_path}")

    return {
        "cost_flow_html": cost_flow_html,
        "final_report_html": html_path,
        "messages": messages,
        "current_step": "visual_output_complete",
    }


def _generate_sankey(
    aarav_billed, priya_billed,
    aarav_plan_b, aarav_plan_a, aarav_oop,
    priya_plan_a, priya_plan_b, priya_oop
) -> str:
    """Generate an interactive Sankey diagram showing money flow."""

    labels = [
        "Aarav's Surgery\n(₹4,50,000)",           # 0
        "Priya's PT Bills\n(₹30,000)",              # 1
        "Plan B Primary\n(Insurer2)",               # 2
        "Plan A Primary\n(Insurer1)",               # 3
        "Plan A Secondary\n(Insurer1)",             # 4
        "Plan B Secondary\n(Insurer2)",             # 5
        "Aarav OOP",                                # 6
        "Priya OOP",                                # 7
        "Insurance Covered",                        # 8
    ]

    source = [0, 0, 0, 1, 1, 1]
    target = [2, 4, 6, 3, 5, 7]
    values = [
        max(0, aarav_plan_b),
        max(0, aarav_plan_a),
        max(0, aarav_oop),
        max(0, priya_plan_a),
        max(0, priya_plan_b),
        max(0, priya_oop),
    ]

    node_colors = [
        "#FF6B6B",   # Aarav billed
        "#FFD93D",   # Priya billed
        "#6BCB77",   # Plan B primary
        "#4D96FF",   # Plan A primary
        "#96C5F7",   # Plan A secondary
        "#B8F0A0",   # Plan B secondary
        "#FF6B6B",   # Aarav OOP (red = cost)
        "#FFD93D",   # Priya OOP (yellow = cost)
        "#6BCB77",   # Insurance covered (green)
    ]

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=25,
            thickness=30,
            line=dict(color="black", width=0.5),
            label=labels,
            color=node_colors,
            hovertemplate="%{label}<br>Amount: ₹%{value:,.0f}<extra></extra>",
        ),
        link=dict(
            source=source,
            target=target,
            value=values,
            color=[
                "rgba(107, 203, 119, 0.5)",
                "rgba(77, 150, 255, 0.4)",
                "rgba(255, 107, 107, 0.5)",
                "rgba(77, 150, 255, 0.5)",
                "rgba(184, 240, 160, 0.5)",
                "rgba(255, 217, 61, 0.5)",
            ],
            hovertemplate="Flow: ₹%{value:,.0f}<extra></extra>",
        )
    )])

    fig.update_layout(
        title=dict(
            text="DuCO-Agent: Insurance Cost Flow — Sen Family (COB Coordination)",
            font=dict(size=18, color="#1a3a5c"),
            x=0.5,
        ),
        font_size=12,
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0a0f1e",
        font_color="white",
        height=500,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    return pyo.plot(fig, output_type="div", include_plotlyjs="cdn", config={"responsive": True})


def _generate_html_report(
    financial: dict,
    cob_aarav: dict, cob_priya: dict,
    cob_reasoning: str, preauth: dict,
    preauth_letters: dict, plan_a: dict, plan_b: dict,
    cost_flow_html: str, today: str,
) -> str:
    """Generate the comprehensive HTML report."""

    family = financial.get("family_summary", {})
    aarav_data = financial.get("aarav", {})
    priya_data = financial.get("priya", {})

    def inr(v):
        if v is None:
            return "—"
        return f"₹{float(v):,.2f}"

    aarav_s = aarav_data.get("summary", {})
    priya_s = priya_data.get("summary", {})
    aarav_primary = aarav_data.get("primary_plan", {})
    aarav_secondary = aarav_data.get("secondary_plan", {})
    priya_primary = priya_data.get("primary_plan", {})
    priya_secondary = priya_data.get("secondary_plan", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DuCO-Agent: COB Report — Sen Family</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0a0f1e;
    --surface: #111827;
    --surface2: #1a2235;
    --border: #1e3a5f;
    --primary: #3b82f6;
    --primary-light: #60a5fa;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --gold: #f59e0b;
    --teal: #06b6d4;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}

  /* Animated gradient header */
  .hero {{
    background: linear-gradient(135deg, #0a0f1e 0%, #1a1a3e 30%, #0d1b40 60%, #0a0f1e 100%);
    padding: 60px 40px;
    text-align: center;
    position: relative;
    overflow: hidden;
    border-bottom: 1px solid var(--border);
  }}
  .hero::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(59,130,246,0.1) 0%, transparent 60%);
    animation: pulse 4s ease-in-out infinite;
  }}
  @keyframes pulse {{ 0%, 100% {{ opacity: 0.5; }} 50% {{ opacity: 1; }} }}
  .hero h1 {{ font-size: 2.5rem; font-weight: 800; background: linear-gradient(90deg, #60a5fa, #a78bfa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; position: relative; }}
  .hero p {{ color: var(--text-muted); font-size: 1rem; margin-top: 8px; position: relative; }}
  .badge {{ display: inline-block; background: rgba(59,130,246,0.2); border: 1px solid var(--primary); color: var(--primary-light); padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; margin: 4px; }}

  .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}

  /* Stats cards row */
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 40px; }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(59,130,246,0.15); }}
  .stat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--card-accent, var(--primary));
  }}
  .stat-card.green {{ --card-accent: var(--success); }}
  .stat-card.blue {{ --card-accent: var(--primary); }}
  .stat-card.orange {{ --card-accent: var(--warning); }}
  .stat-card.red {{ --card-accent: var(--danger); }}
  .stat-label {{ font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
  .stat-value {{ font-size: 1.8rem; font-weight: 800; color: var(--text); }}
  .stat-sub {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }}

  /* Section styles */
  .section {{ margin-bottom: 40px; }}
  .section-title {{
    font-size: 1.1rem; font-weight: 700; color: var(--text);
    border-left: 4px solid var(--primary);
    padding-left: 12px;
    margin-bottom: 20px;
  }}

  /* Cards */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 20px;
  }}

  /* COB flow visual */
  .cob-flow {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
  .cob-box {{
    flex: 1; min-width: 140px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    font-size: 0.85rem;
  }}
  .cob-box strong {{ display: block; font-size: 1rem; margin-bottom: 4px; }}
  .cob-box.primary {{ border-color: var(--success); background: rgba(16, 185, 129, 0.08); }}
  .cob-box.secondary {{ border-color: var(--primary); background: rgba(59, 130, 246, 0.08); }}
  .cob-arrow {{ font-size: 1.5rem; color: var(--text-muted); }}
  .cob-box.patient {{ border-color: var(--warning); background: rgba(245, 158, 11, 0.08); }}

  /* Financial breakdown table */
  .breakdown-table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  .breakdown-table th {{
    background: rgba(59, 130, 246, 0.2);
    color: var(--primary-light);
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .breakdown-table td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); }}
  .breakdown-table tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .breakdown-table .label-col {{ color: var(--text-muted); font-weight: 500; }}
  .breakdown-table .amount-col {{ font-weight: 700; text-align: right; font-family: monospace; }}
  .breakdown-table .plan-b-col {{ color: var(--success); text-align: right; font-weight: 700; font-family: monospace; }}
  .breakdown-table .plan-a-col {{ color: var(--primary-light); text-align: right; font-weight: 700; font-family: monospace; }}
  .breakdown-table .oop-col {{ color: var(--warning); text-align: right; font-weight: 700; font-family: monospace; }}
  .breakdown-table .total-row td {{ background: rgba(59,130,246,0.1); font-weight: 800; border-top: 2px solid var(--border); }}

  /* Pre-auth pills */
  .preauth-pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; margin: 2px; }}
  .preauth-required {{ background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }}
  .preauth-ok {{ background: rgba(16,185,129,0.2); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.4); }}

  /* COB reasoning block */
  .reasoning-block {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    font-size: 0.9rem;
    line-height: 1.8;
    color: var(--text-muted);
    white-space: pre-line;
  }}
  .reasoning-block strong, .reasoning-block b {{ color: var(--text); }}

  /* Tag chips */
  .tag {{ display: inline-block; background: rgba(59,130,246,0.15); color: var(--primary-light); border: 1px solid rgba(59,130,246,0.3); padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; margin: 2px; }}

  /* Letter links */
  .letter-card {{
    display: flex; align-items: center; gap: 16px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
    transition: transform 0.15s;
  }}
  .letter-card:hover {{ transform: translateX(4px); }}
  .letter-icon {{ font-size: 2rem; }}
  .letter-info strong {{ display: block; font-size: 0.95rem; }}
  .letter-info span {{ font-size: 0.8rem; color: var(--text-muted); }}

  /* Footer */
  .footer {{ text-align: center; padding: 40px; color: var(--text-muted); font-size: 0.75rem; border-top: 1px solid var(--border); margin-top: 40px; }}

  /* Sankey wrapper */
  .sankey-wrapper {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }}

  /* Progress bars */
  .prog-bar {{ background: var(--border); border-radius: 999px; height: 10px; overflow: hidden; margin: 4px 0; }}
  .prog-fill {{ height: 100%; border-radius: 999px; transition: width 0.8s ease; }}

  @media (max-width: 768px) {{
    .hero h1 {{ font-size: 1.6rem; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .cob-flow {{ flex-direction: column; }}
  }}
</style>
</head>
<body>

<!-- ═══════════════════════════ HERO ═══════════════════════════ -->
<div class="hero">
  <h1>🏥 DuCO-Agent Report</h1>
  <p>Dual Coverage Optimization — Sen Family | Mumbai, India</p>
  <div style="margin-top:16px;">
    <span class="badge">🤖 LangGraph Agent</span>
    <span class="badge">[DOC] Multi-Modal Inputs</span>
    <span class="badge">⚖️ COB Coordination</span>
    <span class="badge">[OK] Pre-Auth Ready</span>
    <span class="badge">📅 {today}</span>
  </div>
</div>

<div class="container">

<!-- ═══════════════════════════ SUMMARY STATS ═══════════════════ -->
<div class="stats-grid">
  <div class="stat-card orange">
    <div class="stat-label">Total Medical Bills</div>
    <div class="stat-value">{inr(family.get('total_medical_bills', 0))}</div>
    <div class="stat-sub">Aarav's surgery + Priya's PT</div>
  </div>
  <div class="stat-card green">
    <div class="stat-label">Insurance Covers</div>
    <div class="stat-value">{inr(family.get('total_covered_by_insurance', 0))}</div>
    <div class="stat-sub">{family.get('coverage_percentage', 0):.1f}% of total bills</div>
  </div>
  <div class="stat-card red">
    <div class="stat-label">Family Out-of-Pocket</div>
    <div class="stat-value">{inr(family.get('total_family_oop', 0))}</div>
    <div class="stat-sub">After dual plan coordination</div>
  </div>
  <div class="stat-card blue">
    <div class="stat-label">Savings (Dual vs Single)</div>
    <div class="stat-value">{inr(family.get('total_savings_from_dual_coverage', 0))}</div>
    <div class="stat-sub">Extra savings from 2nd plan</div>
  </div>
  <div class="stat-card blue">
    <div class="stat-label">Plan A Total Pays</div>
    <div class="stat-value">{inr(family.get('plan_a_total_pays', 0))}</div>
    <div class="stat-sub">Insurer1 (Primary for Priya / Secondary for Aarav)</div>
  </div>
  <div class="stat-card green">
    <div class="stat-label">Plan B Total Pays</div>
    <div class="stat-value">{inr(family.get('plan_b_total_pays', 0))}</div>
    <div class="stat-sub">Insurer2 (Primary for Aarav / Secondary for Priya)</div>
  </div>
</div>

<!-- Coverage progress bar -->
<div class="card" style="margin-bottom:40px;">
  <div class="section-title">Coverage Overview</div>
  <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-muted); margin-bottom:6px;">
    <span>Insurance</span><span>Patient OOP</span>
  </div>
  <div class="prog-bar">
    <div class="prog-fill" style="width:{family.get('coverage_percentage',0):.1f}%; background: linear-gradient(90deg, #10b981, #3b82f6);"></div>
  </div>
  <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Insurance covers {family.get('coverage_percentage',0):.1f}% of total billed amount</div>
</div>

<!-- ═══════════════════════════ COB DETERMINATION ═══════════════ -->
<div class="section">
  <div class="section-title">⚖️ Coordination of Benefits (COB) Determination</div>

  <!-- Aarav COB -->
  <div class="card">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
      <span style="font-size:2rem;">🦵</span>
      <div>
        <strong>Aarav Sen — ACL Reconstruction Surgery</strong>
        <div style="color:var(--text-muted); font-size:0.85rem;">CPT 29888 + CPT 29881 | Total Billed: {inr(aarav_data.get('total_billed', 0))}</div>
      </div>
    </div>
    <div class="cob-flow">
      <div class="cob-box primary">
        <strong>1️⃣ Plan B (Insurer2)</strong>
        PremiumShield Platinum<br>
        <span style="color:var(--success);">PRIMARY PAYER</span><br>
        <small>Aarav is subscriber</small>
      </div>
      <div class="cob-arrow">→</div>
      <div class="cob-box secondary">
        <strong>2️⃣ Plan A (Insurer1)</strong>
        CorporateCare Gold<br>
        <span style="color:var(--primary-light);">SECONDARY PAYER</span><br>
        <small>Aarav is dependent</small>
      </div>
      <div class="cob-arrow">→</div>
      <div class="cob-box patient">
        <strong>👤 Aarav OOP</strong>
        <span style="color:var(--warning);">{inr(aarav_s.get('patient_oop', 0))}</span><br>
        <small>Final out-of-pocket</small>
      </div>
    </div>
    <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;">
      <strong>COB Rule:</strong> {cob_aarav.get('cob_rule_applied', 'Subscriber Rule')}
    </div>
  </div>

  <!-- Priya COB -->
  <div class="card">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
      <span style="font-size:2rem;">🏃</span>
      <div>
        <strong>Priya Sen — Physical Therapy (Chronic Back Pain)</strong>
        <div style="color:var(--text-muted); font-size:0.85rem;">CPT 97161 + CPT 97110 (×5) | Total Billed: {inr(priya_data.get('total_billed', 0))}</div>
      </div>
    </div>
    <div class="cob-flow">
      <div class="cob-box primary" style="border-color:var(--primary);">
        <strong>1️⃣ Plan A (Insurer1)</strong>
        CorporateCare Gold<br>
        <span style="color:var(--primary-light);">PRIMARY PAYER</span><br>
        <small>Priya is subscriber</small>
      </div>
      <div class="cob-arrow">→</div>
      <div class="cob-box secondary" style="border-color:var(--success);">
        <strong>2️⃣ Plan B (Insurer2)</strong>
        PremiumShield Platinum<br>
        <span style="color:var(--success);">SECONDARY PAYER</span><br>
        <small>Priya is dependent</small>
      </div>
      <div class="cob-arrow">→</div>
      <div class="cob-box patient">
        <strong>👤 Priya OOP</strong>
        <span style="color:var(--warning);">{inr(priya_s.get('patient_oop', 0))}</span><br>
        <small>Final out-of-pocket</small>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════ COST FLOW SANKEY ════════════════ -->
<div class="section">
  <div class="section-title">📊 Insurance Cost Flow Diagram</div>
  <div class="sankey-wrapper">
    {cost_flow_html if cost_flow_html else '<div style="padding:40px;text-align:center;color:var(--text-muted);">Sankey diagram requires Plotly — install with: pip install plotly</div>'}
  </div>
</div>

<!-- ═══════════════════════════ FINANCIAL BREAKDOWN ═════════════ -->
<div class="section">
  <div class="section-title">[CALC] Detailed Financial Breakdown</div>

  <!-- Aarav breakdown -->
  <div class="card">
    <div style="font-weight:700; font-size:1rem; margin-bottom:16px; color:var(--primary-light);">🦵 Aarav's ACL Surgery — Step-by-Step Calculation</div>
    <table class="breakdown-table">
      <thead>
        <tr>
          <th>Description</th>
          <th style="text-align:right;">Plan B (Primary)</th>
          <th style="text-align:right;">Plan A (Secondary)</th>
          <th style="text-align:right;">Patient OOP</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="label-col">Total Billed</td>
          <td class="amount-col" colspan="3" style="text-align:right;">{inr(aarav_data.get('total_billed', 0))}</td>
        </tr>
        <tr>
          <td class="label-col">Annual Deductible</td>
          <td class="plan-b-col">{inr(aarav_primary.get('deductible', 0))}</td>
          <td class="plan-a-col">{inr(aarav_secondary.get('deductible', 0))}</td>
          <td>—</td>
        </tr>
        <tr>
          <td class="label-col">Deductible Applied This Claim</td>
          <td class="plan-b-col">{inr(aarav_primary.get('deductible_applied', 0))}</td>
          <td class="plan-a-col">{inr(aarav_secondary.get('deductible_applied', 0))}</td>
          <td>—</td>
        </tr>
        <tr>
          <td class="label-col">Coinsurance Rate (Plan/Member)</td>
          <td class="plan-b-col">75% / 25%</td>
          <td class="plan-a-col">80% / 20%</td>
          <td>—</td>
        </tr>
        <tr>
          <td class="label-col">Plan Pays</td>
          <td class="plan-b-col">{inr(aarav_s.get('plan_b_pays', 0))}</td>
          <td class="plan-a-col">{inr(aarav_s.get('plan_a_pays', 0))}</td>
          <td>—</td>
        </tr>
        <tr class="total-row">
          <td class="label-col">TOTAL PATIENT OOP</td>
          <td colspan="2" style="text-align:center; color:var(--text-muted);">After both plans pay</td>
          <td class="oop-col">{inr(aarav_s.get('patient_oop', 0))}</td>
        </tr>
        <tr>
          <td class="label-col">💚 Dual Coverage Savings</td>
          <td colspan="3" style="text-align:right; color:var(--success); font-weight:700;">{inr(aarav_s.get('savings_from_dual_coverage', 0))} saved vs. single plan</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Priya breakdown -->
  <div class="card">
    <div style="font-weight:700; font-size:1rem; margin-bottom:16px; color:var(--teal);">🏃 Priya's Physical Therapy — Step-by-Step Calculation</div>
    <table class="breakdown-table">
      <thead>
        <tr>
          <th>Description</th>
          <th style="text-align:right;">Plan A (Primary)</th>
          <th style="text-align:right;">Plan B (Secondary)</th>
          <th style="text-align:right;">Patient OOP</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="label-col">CPT 97161 — PT Evaluation (×1)</td>
          <td class="plan-a-col" colspan="3" style="text-align:right;">Billed: ₹5,000 | Allowed: ₹3,500</td>
        </tr>
        <tr>
          <td class="label-col">CPT 97110 — Therapeutic Exercise (×5)</td>
          <td class="plan-a-col" colspan="3" style="text-align:right;">Billed: ₹25,000 | Allowed: ₹15,000</td>
        </tr>
        <tr>
          <td class="label-col">Deductible Already Met (YTD)</td>
          <td class="plan-a-col">{inr(priya_primary.get('deductible_already_met', 0))}</td>
          <td class="plan-b-col">{inr(priya_secondary.get('deductible_already_met', 0))}</td>
          <td>—</td>
        </tr>
        <tr>
          <td class="label-col">Deductible Applied This Claim</td>
          <td class="plan-a-col">{inr(priya_primary.get('deductible_applied', 0))}</td>
          <td class="plan-b-col">{inr(priya_secondary.get('deductible_applied', 0))}</td>
          <td>—</td>
        </tr>
        <tr>
          <td class="label-col">Plan Pays</td>
          <td class="plan-a-col">{inr(priya_s.get('plan_a_pays', 0))}</td>
          <td class="plan-b-col">{inr(priya_s.get('plan_b_pays', 0))}</td>
          <td>—</td>
        </tr>
        <tr class="total-row">
          <td class="label-col">TOTAL PATIENT OOP</td>
          <td colspan="2" style="text-align:center; color:var(--text-muted);">After both plans pay</td>
          <td class="oop-col">{inr(priya_s.get('patient_oop', 0))}</td>
        </tr>
        <tr>
          <td class="label-col">💚 Dual Coverage Savings</td>
          <td colspan="3" style="text-align:right; color:var(--success); font-weight:700;">{inr(priya_s.get('savings_from_dual_coverage', 0))} saved vs. single plan</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- ═══════════════════════════ PRE-AUTH STATUS ══════════════════ -->
<div class="section">
  <div class="section-title">📋 Pre-Authorization Status</div>
  <div class="card">
    <table class="breakdown-table">
      <thead>
        <tr>
          <th>CPT Code</th>
          <th>Description</th>
          <th>Patient</th>
          <th>Plan A</th>
          <th>Plan B</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''<tr>
          <td><span class="tag">{cpt}</span></td>
          <td style="font-size:0.8rem;">{info.get("description", "")[:60]}</td>
          <td>{info.get("patient", "")}</td>
          <td>{"<span class='preauth-pill preauth-required'>[WARN] Required</span>" if info.get("plan_a_required") else "<span class='preauth-pill preauth-ok'>[OK] Not Required</span>"}</td>
          <td>{"<span class='preauth-pill preauth-required'>[WARN] Required</span>" if info.get("plan_b_required") else "<span class='preauth-pill preauth-ok'>[OK] Not Required</span>"}</td>
        </tr>''' for cpt, info in preauth.items())}
      </tbody>
    </table>
  </div>

  <!-- Pre-auth letters -->
  <div class="section-title" style="margin-top:24px;">[DOC] Generated Pre-Authorization Letters</div>
  <div class="letter-card">
    <span class="letter-icon">[DOC]</span>
    <div class="letter-info">
      <strong>Pre-Authorization Request — Plan A (Insurer1)</strong>
      <span>CPT 29888 + CPT 29881 | Aarav Sen | CorporateCare Gold Plan</span>
    </div>
    <span class="badge">PDF Generated</span>
  </div>
  <div class="letter-card">
    <span class="letter-icon">[DOC]</span>
    <div class="letter-info">
      <strong>Pre-Authorization Request — Plan B (Insurer2)</strong>
      <span>CPT 29888 + CPT 29881 | Aarav Sen | PremiumShield Platinum Plan</span>
    </div>
    <span class="badge">PDF Generated</span>
  </div>
</div>

<!-- ═══════════════════════════ COB REASONING ═══════════════════ -->
<div class="section">
  <div class="section-title">🧠 COB Reasoning (AI Explanation)</div>
  <div class="reasoning-block">{cob_reasoning or "COB reasoning not available."}</div>
</div>

<!-- ═══════════════════════════ CLINICAL CODES ══════════════════ -->
<div class="section">
  <div class="section-title">🏷️ Clinical Codes Summary</div>
  <div class="card">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
      <div>
        <div style="font-weight:600; color:var(--primary-light); margin-bottom:12px;">CPT Codes — Aarav (Surgery)</div>
        <span class="tag">29888 — ACL Reconstruction</span>
        <span class="tag">29881 — Meniscectomy</span>
        <div style="font-weight:600; color:var(--teal); margin-bottom:12px; margin-top:16px;">CPT Codes — Priya (PT)</div>
        <span class="tag">97161 — PT Evaluation</span>
        <span class="tag">97110 — Therapeutic Exercise ×5</span>
      </div>
      <div>
        <div style="font-weight:600; color:var(--warning); margin-bottom:12px;">ICD-10 — Aarav</div>
        <span class="tag">M23.619 — ACL Tear, Right Knee</span>
        <span class="tag">M23.209 — Meniscal Tear</span>
        <span class="tag">S83.511A — ACL Sprain</span>
        <div style="font-weight:600; color:var(--warning); margin-bottom:12px; margin-top:16px;">ICD-10 — Priya</div>
        <span class="tag">M54.5 — Low Back Pain</span>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════ FOOTER ══════════════════════════ -->
<div class="footer">
  <p>🤖 Generated by <strong>DuCO-Agent</strong> — LangGraph Multi-Modal AI System</p>
  <p>Generated on {today}</p>
  <p style="margin-top:8px;">For informational purposes only. Always verify with your insurance provider.</p>
</div>

</div>
</body>
</html>"""
    return html
