# 🏥 DuCO-Agent: Dual Coverage Optimization AI System

> An Agentic, Multi-Modal AI System for Insurance Coordination of Benefits (COB)

DuCO-Agent is an AI-powered pipeline built with LangGraph and Google's Gemini models. It automates the complex process of healthcare insurance Coordination of Benefits (COB) when a patient has dual coverage (e.g., primary and secondary insurance plans).

By ingesting multi-modal medical documents (PDFs, images, and text), the agent infers medical codes, checks pre-authorization requirements, applies COB subscriber rules, calculates complex out-of-pocket costs, and generates professional documentation.

---

## ✨ Key Features

- **Multi-Modal Ingestion:** Extracts data from medical invoices (PNG/JPG), MRI reports (PDF), and patient queries (Text) using Gemini Vision and PyMuPDF.
- **Agentic Workflow:** An 8-step LangGraph state machine with reflection loops and conditional routing.
- **Clinical Code Inference:** Automatically maps medical procedures to CPT and ICD-10 codes with validation retries.
- **COB Logic Engine:** Determines Primary vs. Secondary payers based on the industry-standard Subscriber Rule.
- **Financial Calculation:** Accurately computes deductibles, coinsurance, total out-of-pocket (OOP) costs, and dual-coverage savings.
- **Automated Documentation:** Generates patient-ready HTML reports, Sankey cost flow diagrams, PDF pre-auth letters, and text-to-speech audio briefs.

---

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have Python 3.10+ installed.

```bash
git clone https://github.com/muhammadnavas/duco-agent-ai-assessment.git
cd duco-agent-ai-assessment
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Copy the environment template and add your Google Gemini API key:

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_api_key
```

### 4. Run the Pipeline

First, generate the necessary mock input documents:
```bash
python mock_inputs/generate_mri_pdf.py
```

Then, execute the full agentic pipeline:
```bash
python main.py
```

To view the LangGraph execution structure in ASCII:
```bash
python main.py --graph
```

### 5. View Results

Once the pipeline completes, check the `outputs/` directory for:
- `duco_report.html` (Interactive dashboard)
- `preauth_letter_plan_a.pdf` (Pre-authorization request)
- `preauth_letter_plan_b.pdf` (Pre-authorization request)
- `audio_brief.mp3` (Spoken summary)

### 6. Run Unit Tests

To verify the mathematical accuracy and COB rules logic of the financial calculation agent:
```bash
python -m pytest tests/
```

---

## 📂 Architecture & Structure

```
duco-agent-ai-assessment/
├── agents/                     # LangGraph agent nodes
│   ├── intake_agent.py         # Multi-modal input parsing
│   ├── code_lookup_agent.py    # CPT/ICD-10 inference
│   ├── preauth_check_agent.py  # Pre-auth determination
│   ├── cob_logic_agent.py      # COB rules application
│   ├── financial_calc_agent.py # Cost calculations
│   ├── letter_gen_agent.py     # PDF generation
│   ├── visual_output_agent.py  # HTML/Sankey report
│   └── audio_brief_agent.py    # Text-to-speech
├── graph/                      # LangGraph state machine
├── mock_apis/                  # Mock Insurer Data (Plan A & B)
├── mock_inputs/                # Test documents (PDFs, images)
├── outputs/                    # Generated reports
├── tools/                      # Shared utilities (OCR, API wrappers)
└── main.py                     # Entry point
```

---

## 👥 Author

**Muhammad Navas** — DuCO-Agent AI System

*Note: DuCO-Agent is a demonstration system built for educational and assessment purposes. It is not intended for real clinical or financial use.*
