# 🏥 DuCO-Agent: Dual Coverage Optimization AI System

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green?logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini-1.5--Pro-orange?logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-Private-red)](.)

> An Agentic, Multi-Modal AI System for Insurance Coordination of Benefits (COB)

---

## 🎯 Problem Statement

Priya and Aarav Sen are a married couple with **dual health insurance coverage**:
- **Plan A (Insurer1):** Priya is Primary Policyholder; Aarav is Dependent
- **Plan B (Insurer2):** Aarav is Primary Policyholder; Priya is Dependent

**Claims:**
- Aarav requires **ACL Reconstruction Surgery** (CPT 29888 + 29881) → ₹4,50,000
- Priya has **Physical Therapy bills** (CPT 97161 + 97110) → ₹30,000

**DuCO-Agent** navigates their dual coverage to minimize out-of-pocket costs.

---

## 🏗️ Architecture

```
Multi-Modal Inputs
├── priya_pt_invoice.png       → Gemini Vision (OCR + CPT inference)
├── aarav_mri_report.pdf       → PyMuPDF + Gemini (clinical NLP)
├── surgeon_estimate.jpg       → Gemini Vision (code extraction)
└── user_query.txt             → Gemini NLP (intent parsing)
         ↓
LangGraph State Machine
├── Node 1: intake_agent        → Parse all 4 inputs
├── Node 2: code_lookup_agent   → Infer/validate CPT + ICD-10 codes
├── Node 3: preauth_check_agent → Determine pre-auth requirements
├── Node 4: cob_logic_agent     → Apply COB rules (Subscriber Rule)
├── Node 5: financial_calc_agent→ Calculate deductibles, coinsurance, OOP
├── Node 6: letter_gen_agent    → Generate pre-auth PDF letters
├── Node 7: visual_output_agent → Sankey chart + HTML report
└── Node 8: audio_brief_agent   → Patient-friendly MP3 summary
         ↓
Outputs
├── outputs/duco_report.html          → Full visual report
├── outputs/preauth_letter_plan_a.pdf → Pre-auth for Insurer1
├── outputs/preauth_letter_plan_b.pdf → Pre-auth for Insurer2
├── outputs/audio_brief.mp3           → Patient audio summary
└── outputs/audio_brief_script.txt    → Text script
```

### LangGraph Flow Diagram

```
START → intake → code_lookup ⟲ (reflection loop if validation fails)
              → preauth_check → cob_logic → financial_calc
              → [conditional] → letter_gen → visual_output → audio_brief → END
```

---

## 📋 COB Logic (Key Business Rules)

| Patient | Claim | Primary Plan | Secondary Plan | Rule Applied |
|---------|-------|-------------|----------------|--------------|
| **Aarav** | ACL Surgery ₹4,50,000 | Plan B (Insurer2) | Plan A (Insurer1) | Subscriber Rule |
| **Priya** | PT Bills ₹30,000 | Plan A (Insurer1) | Plan B (Insurer2) | Subscriber Rule |

**The Subscriber Rule:** The plan where you ARE the primary policyholder (employee) always pays BEFORE the plan where you are a dependent.

---

## 💰 Financial Breakdown

### Plan Configurations

| Parameter | Plan A (Insurer1) | Plan B (Insurer2) |
|-----------|------------------|------------------|
| Primary Holder | Priya Sen | Aarav Sen |
| Annual Deductible | ₹20,000 | ₹25,000 |
| Coinsurance | 80% / 20% | 75% / 25% |
| OOP Maximum | ₹2,00,000 | ₹2,50,000 |

### Results

| Claim | Total Billed | Insurance Pays | Patient OOP | Savings |
|-------|-------------|----------------|-------------|---------|
| Aarav's ACL Surgery | ₹4,50,000 | ~₹3,89,000 | ~₹61,000 | ~₹88,750 |
| Priya's PT | ₹30,000 | ~₹20,600 | ~₹9,400 | ~₹9,350 |
| **FAMILY TOTAL** | **₹4,80,000** | **~₹4,09,600** | **~₹70,400** | **~₹98,100** |

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.10+
python --version

# Clone / download repo
cd duco-agent-ai-assessment
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your Google API key
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4. Generate Mock Inputs

```bash
# Generate the MRI PDF report
python mock_inputs/generate_mri_pdf.py
```

### 5. Run DuCO-Agent

```bash
# Full pipeline
python main.py

# Just setup mock files
python main.py --setup

# View graph structure
python main.py --graph
```

### 6. View Results

Open `outputs/duco_report.html` in your browser for the full interactive report.

---

## 📂 Project Structure

```
duco-agent-ai-assessment/
├── .github/
│   └── BRANCH_PROTECTION.md    ← Git workflow rules
├── agents/                     ← LangGraph agent nodes
│   ├── intake_agent.py         ← Multi-modal input parsing
│   ├── code_lookup_agent.py    ← CPT/ICD-10 inference
│   ├── preauth_check_agent.py  ← Pre-auth determination
│   ├── cob_logic_agent.py      ← COB rules application
│   ├── financial_calc_agent.py ← Precise INR calculations
│   ├── letter_gen_agent.py     ← PDF letter generation
│   ├── visual_output_agent.py  ← HTML report + Sankey
│   └── audio_brief_agent.py    ← Patient TTS summary
├── graph/
│   └── duco_graph.py           ← LangGraph state machine
├── mock_apis/
│   ├── insurer1_plan_a.py      ← Plan A FastAPI mock
│   └── insurer2_plan_b.py      ← Plan B FastAPI mock
├── mock_inputs/
│   ├── priya_pt_invoice.png    ← AI-generated PT invoice
│   ├── aarav_mri_report.pdf    ← Generated MRI report
│   ├── surgeon_estimate.jpg    ← AI-generated billing sheet
│   └── user_query.txt          ← Voice transcript
├── outputs/                    ← Generated at runtime
│   ├── duco_report.html
│   ├── preauth_letter_plan_a.pdf
│   ├── preauth_letter_plan_b.pdf
│   └── audio_brief.mp3
├── tools/
│   ├── image_parser.py         ← Gemini Vision wrapper
│   ├── pdf_parser.py           ← PyMuPDF + Gemini
│   └── cpt_icd_mapper.py       ← Code lookup database
├── main.py                     ← Entry point
├── requirements.txt
└── .env.example
```

---

## 🌿 Git Branch Strategy

```
main (protected — no direct commits)
├── feature/intake-agent        ← Steps 1-2: Parsing
├── feature/cob-logic           ← Steps 3-5: COB + financials
└── feature/multi-modal-outputs ← Steps 6-8: Letters + visuals
```

### Semantic Commit Examples
```bash
feat(intake): add Gemini vision parsing for PT invoice images
feat(cob): implement subscriber rule COB determination logic
feat(financial): add dual-coverage savings calculation in INR
feat(letters): generate PDF pre-auth letters for Plan A and B
docs(readme): add setup instructions and API key configuration
```

---

## 🤖 Agentic Features

| Feature | Implementation |
|---------|---------------|
| **Multi-Modal Ingestion** | Gemini Vision (images) + PyMuPDF (PDF) + Gemini NLP (text) |
| **Tool Use** | CPT/ICD-10 lookup DB, Mock Insurance APIs |
| **Reflection Loop** | Code validation with automatic retry (max 2) |
| **State Management** | LangGraph TypedDict state with annotated message accumulation |
| **Conditional Routing** | Pre-auth → letter gen or skip |
| **LLM Reasoning** | Gemini 1.5 Pro for COB explanation |
| **Checkpointing** | MemorySaver for conversation persistence |

---

## 📄 Technical Highlights

| Rubric Category | Implementation |
|----------------|----------------|
| **Agentic Autonomy (40%)** | LangGraph state machine with reflection loops, conditional routing, tool calls, validation |
| **Multi-Modal Integration (20%)** | Gemini Vision for images, PyMuPDF + Gemini NLP for PDFs, text NLP |
| **Mathematical Accuracy (20%)** | Precise deductible, coinsurance, OOP math with INR; non-duplication COB method |
| **Output Aesthetics (20%)** | Dark-mode HTML report, Sankey diagram, professional PDF letters, TTS audio |

---

## 👥 Team

Muhammad Navas — DuCO-Agent AI System

---

*DuCO-Agent is for assessment/educational purposes only. Not for clinical use.*
