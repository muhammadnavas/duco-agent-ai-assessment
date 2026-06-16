"""
agents/audio_brief_agent.py
----------------------------
STEP 8: Audio Brief Agent
Generates a patient-friendly audio summary of the COB results.
Uses Google Text-to-Speech (gTTS) to create an MP3 file.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


def run_audio_brief_agent(state: dict) -> dict:
    """
    Audio Brief Agent:
    - Generates a patient-friendly script summarizing the COB outcome
    - Converts to MP3 using gTTS
    - Returns the text and audio file path
    """
    financial = state.get("financial_breakdown", {})
    cob_aarav = state.get("cob_aarav", {})
    cob_priya = state.get("cob_priya", {})
    preauth_letters = state.get("preauth_letters", {})
    messages = []

    family = financial.get("family_summary", {})
    aarav_s = financial.get("aarav", {}).get("summary", {})
    priya_s = financial.get("priya", {}).get("summary", {})

    def fmt(v):
        return f"Rupees {int(float(v)):,}" if v else "zero"

    total_bills = fmt(family.get("total_medical_bills", 480000))
    total_covered = fmt(family.get("total_covered_by_insurance", 0))
    total_oop = fmt(family.get("total_family_oop", 0))
    aarav_oop = fmt(aarav_s.get("patient_oop", 0))
    priya_oop = fmt(priya_s.get("patient_oop", 0))
    savings = fmt(family.get("total_savings_from_dual_coverage", 0))
    coverage_pct = family.get("coverage_percentage", 0)

    # ── Generate Patient-Friendly Script ──────────────────────
    script = f"""
Hello, Aarav and Priya. This is your DuCO Agent financial briefing for your insurance claim coordination.

Here's what we found after analyzing all your documents and coordinating between both your insurance plans.

SECTION ONE: WHICH PLAN PAYS FIRST.

For Aarav's A.C.L. knee surgery: Your Plan B through Insurer 2 will pay first because Aarav is the primary policyholder on that plan. After Plan B pays, your Plan A through Insurer 1 will step in as the secondary payer to cover additional costs, since Aarav is a dependent on Priya's plan.

For Priya's physical therapy bills: Your Plan A through Insurer 1 will pay first because Priya is the primary policyholder on that plan. After Plan A pays, Plan B through Insurer 2 will pay as secondary.

This is called the Subscriber Rule — the plan where you are the main employee always pays before the plan where you are listed as a dependent.

SECTION TWO: YOUR FINANCIAL BREAKDOWN.

Your combined medical bills total {total_bills}.

Your combined insurance coverage between both plans will cover {total_covered}, which is approximately {coverage_pct:.0f} percent of your total bills.

For Aarav's surgery of {fmt(financial.get('aarav', {}).get('total_billed', 450000))}: Your out-of-pocket cost after both plans coordinate will be {aarav_oop}.

For Priya's physical therapy bills: Your out-of-pocket cost will be {priya_oop}.

Your TOTAL family out-of-pocket cost is {total_oop}. And because you have dual coverage, you are saving an estimated {savings} compared to if you only had a single insurance plan.

SECTION THREE: PRE-AUTHORIZATION.

We have generated pre-authorization request letters for both Plan A and Plan B for Aarav's surgery. These letters include the CPT codes 29888 for A.C.L. reconstruction and 29881 for meniscectomy, along with the supporting diagnosis codes from Aarav's M.R.I. report. 

IMPORTANT: Please submit these pre-authorization letters to both insurance companies BEFORE scheduling the surgery to avoid claim rejection.

SECTION FOUR: ACTION ITEMS.

One. Submit the pre-authorization letter to Insurer 1, Plan A, immediately.
Two. Submit the pre-authorization letter to Insurer 2, Plan B, immediately.
Three. Ensure the hospital submits the claim to Plan B first, then Plan A.
Four. For Priya's physical therapy: submit to Plan A first, then Plan B.

You are well-covered with dual insurance. By coordinating your benefits correctly, you are maximizing your protection and minimizing your out-of-pocket costs. 

If you have any questions, please consult your HR benefits coordinator or call both insurance companies directly.

This has been your DuCO Agent briefing. Good luck with the surgery, Aarav!
""".strip()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, "audio_brief.mp3")
    script_path = os.path.join(output_dir, "audio_brief_script.txt")

    # Save text script
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    # Generate audio
    if GTTS_AVAILABLE:
        try:
            tts = gTTS(text=script, lang="en", slow=False, tld="co.in")
            tts.save(audio_path)
            print(f"  ✅ Audio brief saved: {audio_path}")
            messages.append(f"✅ Audio brief generated: {audio_path}")
        except Exception as e:
            print(f"  ⚠️  Audio generation failed: {e}")
            audio_path = None
            messages.append(f"⚠️  Audio generation failed: {str(e)[:100]}")
    else:
        print("  ⚠️  gTTS not installed — audio skipped. Install with: pip install gTTS")
        audio_path = None
        messages.append("⚠️  gTTS not installed — audio script saved as text only")

    print("  ✅ DuCO-Agent pipeline complete! 🎉")
    messages.append("✅ DuCO-Agent full pipeline COMPLETE")

    return {
        "audio_brief_text": script,
        "audio_brief_path": audio_path or script_path,
        "messages": messages,
        "current_step": "pipeline_complete",
        "is_complete": True,
    }
