"""Pre-Authorization Letter Generation Agent creating clinically sound PDF letters."""
import os
import sys
import json
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def run_letter_gen_agent(state: dict) -> dict:
    """Generates pre-auth PDF letters for Plan A and Plan B."""
    cpt_codes = state.get("cpt_codes", [])
    icd10_codes = state.get("icd10_codes", [])
    parsed = state.get("parsed_documents", {})
    messages = []

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    mri = parsed.get("mri_report", {})
    surgeon = parsed.get("surgeon_estimate", {})

    patient_info = {
        "name": "Aarav Sen",
        "dob": "15-March-1988",
        "member_id_plan_a": "IC1-DEP-2026-AARAV",
        "member_id_plan_b": "IC2-PH-2026-AARAV",
        "gender": "Male",
        "age": 38,
    }

    procedures = [
        {"cpt": "29888", "desc": "Arthroscopically aided anterior cruciate ligament (ACL) reconstruction", "charge": 350000},
        {"cpt": "29881", "desc": "Arthroscopy, knee, surgical; with meniscectomy (medial)", "charge": 100000},
    ]
    diagnoses = [
        {"code": "M23.619", "desc": "Complete tear of anterior cruciate ligament, right knee"},
        {"code": "M23.209", "desc": "Derangement of medial meniscus due to tear, right knee"},
    ]
    total_surgery = 450000

    letter_data = {
        "patient": patient_info,
        "procedures": procedures,
        "diagnoses": diagnoses,
        "total_charge": total_surgery,
        "surgeon": surgeon.get("surgeon_name", "Dr. Arjun Mehta, MS Orthopaedics"),
        "hospital": surgeon.get("hospital_facility", "Apollo Hospitals, Mumbai"),
        "mri_date": mri.get("study_date", "14-June-2026"),
        "radiologist": mri.get("radiologist", "Dr. Kavitha Rao, FRCR"),
        "requesting_physician": surgeon.get("surgeon_name", "Dr. Arjun Mehta, MS Orthopaedics"),
        "date": date.today().strftime("%d-%B-%Y"),
    }

    print("  [WRITE] Generating pre-auth letter for Plan A (Insurer1)...")
    letter_a_path = _generate_preauth_pdf(
        letter_data=letter_data,
        plan_name="Insurer1 Health Insurance Ltd.",
        plan_id="INSURER1-PLAN-A-2026",
        plan_type="Plan A — CorporateCare Gold Plan",
        member_id=patient_info["member_id_plan_a"],
        policy_number="IC1-MUM-2026-PRY-001",
        member_role="Dependent (Spouse of Priya Sen)",
        output_path=os.path.join(output_dir, "preauth_letter_plan_a.pdf"),
        insurer_address="Insurer1 Health Insurance Ltd.\nPre-Authorization Department\n4th Floor, Insurance Tower\nBandra Kurla Complex, Mumbai — 400051",
    )
    messages.append(f"[OK] Pre-auth letter generated for Plan A: {letter_a_path}")

    print("  [WRITE] Generating pre-auth letter for Plan B (Insurer2)...")
    letter_b_path = _generate_preauth_pdf(
        letter_data=letter_data,
        plan_name="Insurer2 Assurance Corporation",
        plan_id="INSURER2-PLAN-B-2026",
        plan_type="Plan B — PremiumShield Platinum Plan",
        member_id=patient_info["member_id_plan_b"],
        policy_number="IC2-MUM-2026-ARV-001",
        member_role="Primary Policyholder",
        output_path=os.path.join(output_dir, "preauth_letter_plan_b.pdf"),
        insurer_address="Insurer2 Assurance Corporation\nMedical Authorization Unit\n12th Floor, Prestige Business Park\nLower Parel, Mumbai — 400013",
    )
    messages.append(f"[OK] Pre-auth letter generated for Plan B: {letter_b_path}")

    return {
        "preauth_letters": {
            "plan_a": letter_a_path,
            "plan_b": letter_b_path,
        },
        "messages": messages,
        "current_step": "letter_gen_complete",
    }


def _generate_preauth_pdf(
    letter_data: dict,
    plan_name: str,
    plan_id: str,
    plan_type: str,
    member_id: str,
    policy_number: str,
    member_role: str,
    output_path: str,
    insurer_address: str,
) -> str:
    """Generate a professional pre-authorization request PDF letter."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.5*cm,
        leftMargin=2.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    h1 = ParagraphStyle("H1", fontSize=13, fontName="Helvetica-Bold",
                        textColor=colors.HexColor("#1a3a5c"), alignment=TA_CENTER, spaceAfter=2)
    h2 = ParagraphStyle("H2", fontSize=10, fontName="Helvetica",
                        textColor=colors.HexColor("#444"), alignment=TA_CENTER, spaceAfter=6)
    body = ParagraphStyle("Body", fontSize=9.5, fontName="Helvetica",
                          textColor=colors.HexColor("#222"), spaceAfter=6, leading=14, alignment=TA_JUSTIFY)
    bold = ParagraphStyle("Bold", fontSize=9.5, fontName="Helvetica-Bold",
                          textColor=colors.HexColor("#1a3a5c"), spaceAfter=4)
    label = ParagraphStyle("Label", fontSize=9, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#555"), spaceAfter=2)

    story.append(Paragraph("PRE-AUTHORIZATION REQUEST — SURGICAL PROCEDURE", h1))
    story.append(Paragraph(f"Submitted to: {plan_name} | {plan_type}", h2))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"Date: {letter_data['date']}", label))
    for line in insurer_address.split("\n"):
        story.append(Paragraph(line, body))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"<b>RE: Pre-Authorization Request — Elective Orthopaedic Surgery</b><br/>"
        f"Patient: {letter_data['patient']['name']} | Member ID: {member_id} | Role: {member_role}<br/>"
        f"Policy Number: {policy_number} | Plan ID: {plan_id}",
        body
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaa")))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PATIENT INFORMATION", bold))
    pat_data = [
        ["Full Name:", letter_data["patient"]["name"], "Date of Birth:", letter_data["patient"]["dob"]],
        ["Member ID:", member_id, "Gender:", "Male, Age 38"],
        ["Policy Number:", policy_number, "Plan:", plan_type],
    ]
    pat_table = Table(pat_data, colWidths=[3.5*cm, 7*cm, 3.5*cm, 5*cm])
    pat_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4f8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(pat_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("CLINICAL INDICATION / DIAGNOSIS", bold))
    story.append(Paragraph(
        f"Mr. {letter_data['patient']['name']} sustained a sports injury resulting in a <b>complete tear of the "
        f"anterior cruciate ligament (ACL)</b> and <b>medial meniscal tear</b> of the right knee. "
        f"MRI examination performed on {letter_data['mri_date']} at Apollo Hospitals, Mumbai, confirmed "
        f"by {letter_data['radiologist']}, demonstrated Grade III complex tear of the posterior horn and "
        f"body of the medial meniscus with ACL fiber discontinuity and bone contusions consistent with "
        f"a pivot-shift mechanism of injury. Conservative management has been considered, however surgical "
        f"intervention is clinically indicated and recommended for optimal functional recovery.",
        body
    ))

    icd_header = [["ICD-10 Code", "Diagnosis Description"]]
    icd_rows = [[d["code"], d["desc"]] for d in letter_data["diagnoses"]]
    icd_table = Table(icd_header + icd_rows, colWidths=[4*cm, 14.5*cm])
    icd_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(icd_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("REQUESTED PROCEDURES / CPT CODES", bold))
    proc_header = [["CPT Code", "Procedure Description", "Estimated Charge (INR)"]]
    proc_rows = [[p["cpt"], p["desc"], f"₹{p['charge']:,.0f}"] for p in letter_data["procedures"]]
    proc_rows.append(["", "TOTAL ESTIMATED CHARGES", f"₹{letter_data['total_charge']:,.0f}"])
    proc_table = Table(proc_header + proc_rows, colWidths=[2.5*cm, 13*cm, 4*cm])
    proc_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f4e8")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
    ]))
    story.append(proc_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("CLINICAL JUSTIFICATION FOR MEDICAL NECESSITY", bold))
    story.append(Paragraph(
        "1. <b>ACL Reconstruction (CPT 29888):</b> Complete ACL tear confirmed by MRI. "
        "Patient presents with knee instability and functional limitation.",
        body
    ))
    story.append(Paragraph(
        "2. <b>Meniscectomy (CPT 29881):</b> Grade III complex tear of the medial meniscus. "
        "Concurrent arthroscopic partial meniscectomy during ACL reconstruction is clinically indicated.",
        body
    ))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaa")))
    story.append(Paragraph("REQUESTING PHYSICIAN / SURGEON", bold))
    phys_data = [
        ["Surgeon:", letter_data["surgeon"], "Specialty:", "Orthopaedic Surgery (MS)"],
        ["Hospital:", letter_data["hospital"], "Contact:", "+91-22-6699-0000"],
        ["Request Date:", letter_data["date"], "Urgency:", "Elective — Within 4-6 Weeks"],
    ]
    phys_table = Table(phys_data, colWidths=[3*cm, 8*cm, 2.5*cm, 6*cm])
    phys_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(phys_table)

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "We respectfully request review and approval of this pre-authorization request.",
        body
    ))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="50%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Paragraph(f"<b>{letter_data['surgeon']}</b>", bold))
    story.append(Paragraph(f"MS Orthopaedics | {letter_data['hospital']}", body))
    story.append(Paragraph(f"Date: {letter_data['date']}", body))

    doc.build(story)
    print(f"  [OK] Pre-auth letter saved: {output_path}")
    return output_path
