"""Script to generate mock_inputs/aarav_mri_report.pdf."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

def generate_mri_report():
    output_path = os.path.join(os.path.dirname(__file__), "aarav_mri_report.pdf")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ---- Header ----
    header_style = ParagraphStyle(
        "Header", fontSize=14, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=colors.HexColor("#1a3a5c"), spaceAfter=2
    )
    sub_header_style = ParagraphStyle(
        "SubHeader", fontSize=10, fontName="Helvetica",
        alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=2
    )
    story.append(Paragraph("APOLLO HOSPITALS", header_style))
    story.append(Paragraph("Department of Radiology & Diagnostic Imaging", sub_header_style))
    story.append(Paragraph("Plot No. 13, Greams Road, Chennai - 600006 | Tel: +91-44-2829-0200", sub_header_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 8))

    # ---- Report Title ----
    title_style = ParagraphStyle(
        "Title", fontSize=13, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=colors.HexColor("#d32f2f"), spaceAfter=6
    )
    story.append(Paragraph("MRI EXAMINATION REPORT — RIGHT KNEE", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 10))

    # ---- Patient Info Table ----
    patient_data = [
        ["Patient Name:", "Aarav Sen", "Study Date:", "14-June-2026"],
        ["Age/Sex:", "38 Years / Male", "Report Date:", "15-June-2026"],
        ["Patient ID:", "APOL-MUM-2026-04872", "Ref. Physician:", "Dr. Arjun Mehta, MS Ortho"],
        ["Contact:", "+91 98765 43210", "Modality:", "MRI 3.0 Tesla"],
        ["Indication:", "Right knee pain, swelling, inability to fully extend knee post sports injury", "", ""],
    ]

    table_style = TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#1a3a5c")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4f8")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f0f4f8"), colors.HexColor("#e8eef5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("SPAN", (1, 4), (3, 4)),
    ])
    t = Table(patient_data, colWidths=[3.5*cm, 7*cm, 3.5*cm, 5.5*cm])
    t.setStyle(table_style)
    story.append(t)
    story.append(Spacer(1, 12))

    # ---- Sections ----
    section_style = ParagraphStyle(
        "Section", fontSize=11, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3a5c"), spaceBefore=10, spaceAfter=4,
        borderPad=4, borderColor=colors.HexColor("#1a3a5c"),
    )
    body_style = ParagraphStyle(
        "Body", fontSize=9.5, fontName="Helvetica",
        textColor=colors.HexColor("#333333"), spaceAfter=4,
        alignment=TA_JUSTIFY, leading=14,
    )
    finding_style = ParagraphStyle(
        "Finding", fontSize=9.5, fontName="Helvetica",
        textColor=colors.HexColor("#333333"),
        spaceAfter=3, leftIndent=15, leading=14,
    )
    critical_style = ParagraphStyle(
        "Critical", fontSize=9.5, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#c62828"), spaceAfter=4, leftIndent=15, leading=14,
    )

    # Technique
    story.append(Paragraph("TECHNIQUE", section_style))
    story.append(Paragraph(
        "MRI examination of the right knee was performed on a 3.0 Tesla superconducting magnet (Siemens MAGNETOM Skyra) "
        "using a dedicated knee coil. Sequences obtained: Coronal PD Fat-Sat, Sagittal PD Fat-Sat, Sagittal T2, "
        "Axial PD, Coronal T1, and 3D isotropic SPACE sequence for multiplanar reformats. No intravenous contrast "
        "was administered. Total scan time: 35 minutes.",
        body_style
    ))

    # Findings
    story.append(Paragraph("FINDINGS", section_style))

    story.append(Paragraph("<b>1. Anterior Cruciate Ligament (ACL):</b>", finding_style))
    story.append(Paragraph(
        "• <b>Complete tear of the anterior cruciate ligament (ACL)</b> is identified. The ACL fibers are discontinuous "
        "with diffuse T2 hyperintense signal throughout the ligament substance. The ligament demonstrates a horizontal "
        "orientation (Blumensaat sign disrupted) with laxity and redundancy of residual fibers. Bone contusions are "
        "noted at the lateral femoral condyle and posterior lateral tibial plateau, consistent with the classic pivot "
        "shift mechanism of injury. ACL footprint: femoral and tibial attachments demonstrate avulsion signal changes.",
        critical_style
    ))

    story.append(Paragraph("<b>2. Posterior Cruciate Ligament (PCL):</b>", finding_style))
    story.append(Paragraph(
        "• Intact. The PCL demonstrates normal low T2 signal intensity with preserved fiber continuity and normal "
        "posterior bow configuration. No signal abnormality or discontinuity.",
        finding_style
    ))

    story.append(Paragraph("<b>3. Medial Meniscus:</b>", finding_style))
    story.append(Paragraph(
        "• <b>Grade III signal abnormality (tear) of the medial meniscus</b> is identified. A complex, oblique tear "
        "is present involving the posterior horn and body of the medial meniscus, extending to the inferior articular "
        "surface. The tear measures approximately 12mm in longitudinal extent. Associated meniscal extrusion of "
        "approximately 3.5mm is noted at the mid-body level. The anterior horn appears intact.",
        critical_style
    ))

    story.append(Paragraph("<b>4. Lateral Meniscus:</b>", finding_style))
    story.append(Paragraph(
        "• Grade I-II intrameniscal signal change is noted in the posterior horn of the lateral meniscus, "
        "not extending to the articular surface. This likely represents intrasubstance degeneration rather "
        "than a true tear. No discrete tear identified.",
        finding_style
    ))

    story.append(Paragraph("<b>5. Medial Collateral Ligament (MCL):</b>", finding_style))
    story.append(Paragraph(
        "• Mild periligamentous edema noted adjacent to the superficial MCL, consistent with Grade I sprain. "
        "No discontinuity of ligament fibers.",
        finding_style
    ))

    story.append(Paragraph("<b>6. Lateral Collateral Ligament / Posterolateral Corner:</b>", finding_style))
    story.append(Paragraph("• Intact. No signal abnormality or fiber disruption identified.", finding_style))

    story.append(Paragraph("<b>7. Patellofemoral Joint:</b>", finding_style))
    story.append(Paragraph(
        "• Mild patellar tendinopathy. Minimal joint effusion with moderate knee joint effusion noted "
        "(estimated 15-20mL). No loose bodies identified. Articular cartilage of the patellofemoral "
        "joint appears intact.",
        finding_style
    ))

    story.append(Paragraph("<b>8. Bone Marrow & Osseous Structures:</b>", finding_style))
    story.append(Paragraph(
        "• Bone marrow contusions at the lateral femoral condyle and posterolateral tibial plateau as described. "
        "No fracture lines identified. No avascular necrosis. Tibial plateau intact.",
        finding_style
    ))

    # Impression
    story.append(Paragraph("IMPRESSION / CONCLUSION", section_style))
    impression_data = [
        ["1.", "COMPLETE TEAR OF THE ANTERIOR CRUCIATE LIGAMENT (ACL) — Right Knee"],
        ["2.", "COMPLEX TEAR OF THE MEDIAL MENISCUS — Posterior horn and body, Grade III"],
        ["3.", "Bone contusions: Lateral femoral condyle and posterolateral tibial plateau (pivot shift pattern)"],
        ["4.", "Grade I MCL sprain"],
        ["5.", "Moderate knee joint effusion"],
    ]
    imp_style = TableStyle([
        ("FONTNAME", (0, 0), (0, 1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (1, 1), colors.HexColor("#c62828")),
        ("TEXTCOLOR", (0, 2), (1, -1), colors.HexColor("#333333")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8f8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ffcccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ])
    imp_t = Table(impression_data, colWidths=[1*cm, 16.5*cm])
    imp_t.setStyle(imp_style)
    story.append(imp_t)
    story.append(Spacer(1, 12))

    # Recommendation
    story.append(Paragraph("CLINICAL RECOMMENDATION", section_style))
    story.append(Paragraph(
        "Given the complete ACL tear with associated medial meniscal tear, <b>surgical intervention is strongly "
        "recommended</b>. The patient is a suitable candidate for arthroscopic ACL reconstruction (CPT 29888) with "
        "concurrent partial medial meniscectomy (CPT 29881). Pre-operative physiotherapy to reduce swelling and "
        "strengthen quadriceps is advisable prior to surgery. Orthopedic surgical consultation is recommended for "
        "definitive treatment planning.",
        body_style
    ))

    # Relevant ICD-10 Codes
    story.append(Paragraph("RELEVANT DIAGNOSTIC CODES (ICD-10-CM)", section_style))
    icd_data = [
        ["ICD-10 Code", "Description"],
        ["M23.619", "Other spontaneous disruption of ACL — Right Knee"],
        ["M23.209", "Derangement of unspecified meniscus — Right Knee (Medial)"],
        ["M25.361", "Stiffness of right knee, NEC"],
        ["S83.511A", "Sprain of ACL of right knee, initial encounter"],
    ]
    icd_style = TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ])
    icd_t = Table(icd_data, colWidths=[4*cm, 13.5*cm])
    icd_t.setStyle(icd_style)
    story.append(icd_t)
    story.append(Spacer(1, 20))

    # Signature
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 8))
    sig_style = ParagraphStyle(
        "Sig", fontSize=9, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3a5c"), spaceAfter=2
    )
    story.append(Paragraph("Dr. Kavitha Rao, MBBS, MD (Radiology), FRCR", sig_style))
    story.append(Paragraph(
        "Senior Consultant Radiologist | Apollo Hospitals, Mumbai\n"
        "Report Date: 15-June-2026 | Digital Signature Verified",
        ParagraphStyle("SigSub", fontSize=8.5, fontName="Helvetica",
                       textColor=colors.HexColor("#666666"))
    ))

    doc.build(story)
    print(f"MRI report PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_mri_report()
