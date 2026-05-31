# 🛡️ Plum Claims AI: Intelligent Multi-Agent Adjudication Pipeline

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Modern_API-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent_State_Machine-purple)

An end-to-end, fault-tolerant health insurance claims adjudication system. This pipeline utilizes a **Multi-Agent Orchestration Model** to extract medical data via AI, validate it through strict deterministic policy engines, and surface actionable, itemized decisions (Approve, Reject, Partial, or Manual Review) via a Streamlit frontend.

---

## 📖 Overview & Critical Problems Solved

Processing medical claims typically forces a tradeoff: **AI is too unpredictable for financial math**, while **traditional code is too rigid for unstructured medical documents**. 

This project solves that by splitting responsibilities. It uses **LLM-based Agents** strictly for unstructured data extraction and passes that clean data to a **100% Deterministic Policy Engine** for financial and medical adjudication.

### 🌟 Core System Merits
* **The "Substring Trap" Elimination:** Uses advanced Regex word-boundary logic to differentiate between distinct medical conditions that share letters (e.g., distinguishing a covered spinal *"herniation"* from an excluded abdominal *"hernia"*).
* **Smart Contextual Keyword Matching:** Extracts heavy-hitting root keywords (e.g., "bariatric", "obesity") from verbose policy JSON strings to accurately catch exclusions even when doctors use varying terminology.
* **Granular Line-Item Adjudication:** Instead of blanket rejections, the engine surgically identifies and rejects excluded line items (like cosmetic teeth whitening) while approving valid underlying treatments (like root canals).
* **Dynamic Patient/Dependent Resolution:** Intelligently maps claims to dependents and fetches the correct primary member's `join_date` to accurately calculate active policy days and waiting periods.
* **Zero Hallucination in Math:** Financial limits, co-pays, and network discounts are handled by pure Python, guaranteeing 100% accuracy and deterministic behavior.

---

## 🏗️ Project Architecture & File Structure

The system is built on a modular state-machine pattern. Below is the structure and purpose of each core file.

```text
C:.
├── frontend.py               # Main Streamlit user interface for claim submission
├── requirements.txt          # Python dependencies
├── run.py                    # Entry point to launch the FastAPI/Streamlit services
│
├── app/
│   ├── orchestrator.py       # The central State Machine linking all agents and engines
│   │
│   ├── agents/
│   │   ├── base.py           # Base class definitions for LLM agents
│   │   ├── extractor.py      # LLM Agent: Converts unstructured images to structured JSON
│   │   ├── gatekeeper.py     # LLM Agent: Pre-flight checks for doc readability and type
│   │   └── verifier.py       # Agent: Cross-references extracted identities vs policy DB
│   │
│   ├── api/
│   │   └── routes.py         # FastAPI endpoints exposing the orchestrator to the frontend
│   │
│   ├── core/
│   │   ├── config.py         # Environment variables and global configurations
│   │   ├── exceptions.py     # Custom error handling for graceful pipeline degradation
│   │   └── state.py          # Pydantic models defining the ClaimState trace object
│   │
│   └── engine/
│       └── adjudicator.py    # The Deterministic Brain: Handles math, rules, limits, & fraud
│
├── data/
│   ├── employee_state.json   # Local DB for tracking fraud velocity (same-day/monthly claims)
│   ├── policy_terms.json     # Highly-configurable insurance rules, limits, and exclusions
│   └── test_cases.json       # JSON configurations for the 12 evaluation edge-cases
│
├── pages/
│   └── eval.py               # Interactive Streamlit Evaluation Dashboard for TC review
│
└── TC/                       # Directory containing all input documents and output screenshots
```

## 🧪 Comprehensive Evaluation (TC-001 to TC-012)

The pipeline was strictly evaluated against 12 real-world medical edge cases. Here is exactly how the system solves each one:

| Test Case | Scenario | How the System Solves It | Decision |
| :--- | :--- | :--- | :--- |
| **TC-001** | **Wrong Document Uploaded** | `gatekeeper.py` analyzes the image intent before processing. It detects two prescriptions instead of a bill, halting the pipeline to save compute. | 🛑 **HALTED** |
| **TC-002** | **Unreadable Document** | `gatekeeper.py` evaluates image clarity/blurriness. It halts the pipeline and specifically asks the user to re-upload the illegible file. | 🛑 **HALTED** |
| **TC-003** | **Name Mismatch** | `verifier.py` cross-references the LLM-extracted patient names against the selected dependent in `state.py`, halting if they belong to different people. | 🛑 **HALTED** |
| **TC-004** | **Clean Approval** | The `orchestrator.py` runs the full pipeline flawlessly, passing valid data to the `adjudicator.py` which applies standard network discounts and copays. | ✅ **APPROVED** |
| **TC-005** | **Waiting Period (Diabetes)** | `adjudicator.py` calculates `days_active` using `join_date`. It uses Regex to match "diabetes" and explicitly calculates the exact future eligibility date. | ❌ **REJECTED** |
| **TC-006** | **Dental Cosmetic Exclusion** | `adjudicator.py` iterates over the `line_items` list. It flags "teeth whitening" via regex, deducts its cost, and approves the rest of the valid bill. | ⚠️ **PARTIAL** |
| **TC-007** | **MRI Pre-Auth Missing** | `adjudicator.py` detects high-value diagnostic keywords ("MRI") exceeding the ₹10,000 threshold and triggers the pre-authorization rejection rule. | ❌ **REJECTED** |
| **TC-008** | **Per-Claim Limit Exceeded** | `adjudicator.py` compares the requested amount against the global ₹5000 `per_claim_limit` and enforces a hard mathematical rejection. | ❌ **REJECTED** |
| **TC-009** | **Fraud Signal** | The engine checks `employee_state.json`. It detects 3+ claims submitted on the exact same date for the same ID, flagging it for review. | 👀 **MANUAL** |
| **TC-010** | **Network Discount** | The engine matches the extracted hospital name against the `network_hospitals` array, correctly applying the % discount *before* copay math. | ✅ **APPROVED** |
| **TC-011** | **Component Failure** | A simulated crash in `extractor.py` is caught by a `try/except` block in the Orchestrator. The confidence score is slashed, preventing a 500 Server Error. | 👀 **MANUAL** |
| **TC-012** | **Excluded Treatment** | A custom text-cleaning function strips generic words ("programs", "surgery") from the policy, isolating keywords like "Obesity" to successfully reject vague doctor notes. | ❌ **REJECTED** |

---

## ⚖️ Pros and Cons

### Pros
* **Highly Transparent:** Every action is logged in an `Agent Audit Trace`, making it incredibly easy for claim adjusters to see *why* an AI made a decision.
* **Cost-Efficient Validation:** The Gatekeeper halts bad requests early, preventing expensive LLM extraction calls on blurry, incorrect, or irrelevant files.
* **Modular Policy Management:** Insurance policies change constantly. By isolating the rules in `policy_terms.json`, business teams can update financial limits without touching Python code.
* **Deterministic Math:** Completely eliminates the risk of an LLM hallucinating a financial calculation.

### Cons
* **Latency:** Calling Vision LLMs to extract data from high-resolution images introduces processing delays (typically 3-8 seconds per document).
* **API Dependency:** The system relies heavily on third-party AI uptime. If the LLM provider goes down, the extraction pipeline stalls.
* **Local State Management:** Currently uses a local JSON file (`employee_state.json`) for fraud tracking, which is not suitable for horizontal scaling or high concurrency.

---

## 🚀 Future Roadmap

* **Custom V-LLM Fine-Tuning (Privacy & Speed):** Migrate away from external third-party API dependencies by fine-tuning an open-weight Vision-Language Model (e.g., Qwen2-VL-7B-Instruct) specifically for medical receipt and prescription entity extraction. Utilizing parameter-efficient techniques like QLoRA and frameworks like LlamaFactory will allow the system to run a highly optimized, domain-specific model locally. This ensures strict patient data privacy and drastically reduces inference latency.
* **Compute & Token Optimization:** Introduce robust pre-LLM checks (using lightweight Python libraries like `PyMuPDF` or `Pillow`) to enforce strict file size limits and maximum page counts. By detecting oversized or structurally flawed documents *before* they hit the AI extraction layer, we drastically reduce token waste, lower compute costs, and speed up rejection times.
* **Database Migration:** Replace the local `employee_state.json` with a robust relational database (e.g., PostgreSQL or Redis) to handle concurrent fraud velocity tracking safely in a production environment.
* **OCR Fallback Layer:** Implement `Tesseract OCR` as a lightweight, local secondary fallback. If the Vision-LLM fails or times out, the system can attempt a traditional text scrape to salvage the claim without failing.
* **Automated Pre-Auth Webhooks:** Add a module that automatically generates a pre-authorization request PDF and fires a webhook to the hospital if a high-value claim is rejected purely for missing authorization.

