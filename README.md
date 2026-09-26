<div align="center">

# PrivacyLens AI

### Understand what matters before accepting long Terms & Conditions.

<p>
  <img src="https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=white" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Groq-F55036?logo=groq&logoColor=white" alt="Groq">
  <img src="https://img.shields.io/badge/Tesseract-OCR-555555" alt="Tesseract OCR">
</p>

<p>
  <a href="#features">Features</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#inputs">Inputs</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#setup">Setup</a>
</p>

</div>

---

## What is PrivacyLens AI?

PrivacyLens AI is a **document and policy analysis tool** that helps users understand long Terms & Conditions, privacy policies, and similar content.

Instead of manually going through hundreds of lines, you provide the content and PrivacyLens AI extracts the important information.

```text
Text / URL / File / Image
            ↓
      Extract Content
            ↓
       Analyze Clauses
            ↓
       Check Evidence
            ↓
      Understand Result
```

---

## Features

* Analyze pasted text
* Analyze public URLs
* Upload documents
* Upload images
* Extract text from multiple file formats
* OCR for image-based content
* Rule-based important-clause detection
* Groq-based fact extraction
* Groq-based summarization
* Customer-focused risk analysis
* Evidence-backed findings
* View relevant source content

---

## How It Works

```text
                    INPUT
                      │
        ┌─────────────┼─────────────┐
        │             │             │
       Text           URL        File / Image
        │             │             │
        └─────────────┼─────────────┘
                      ↓
              CONTENT EXTRACTION
                      ↓
               TEXT PROCESSING
                      ↓
             CLAUSE DETECTION
                      ↓
          ┌───────────┴───────────┐
          │                       │
     Rule-Based                 Groq
      Analysis                   LLM
          │                       │
          └───────────┬───────────┘
                      ↓
                EVIDENCE CHECK
                      ↓
                 FINAL RESULT
```

---

## What It Analyzes

PrivacyLens AI looks for customer-relevant conditions such as:

```text
Payment & Fees
Refunds & Cancellation
Automatic Renewal
Data Collection
Data Sharing
Cookies & Tracking
Advertising & Profiling
Data Retention
Arbitration
Liability
Account Termination
Content Permissions
AI / Model Usage
```

A keyword match alone is **not treated as a risk**.

Detected information passes through predefined conditions before it is shown as a finding.

---

## Result

The final result is divided into three simple sections:

```text
┌─────────────────────────────────┐
│             SUMMARY             │
│  What is this document about?   │
├─────────────────────────────────┤
│       RISKS FOR PURCHASER       │
│  What should the customer      │
│  pay attention to?              │
├─────────────────────────────────┤
│         THINGS TO KNOW          │
│  Supporting facts + source      │
└─────────────────────────────────┘
```

### Summary

A short explanation of the document and its main user-facing terms.

### Risks for the Purchaser

Customer-focused findings around areas such as:

```text
Money
Privacy
Tracking
Retention
Cancellation
Contracts
Content Rights
AI / Model Usage
```

### Things to Know

Supporting facts with a **View Source** option.

---

# Inputs

<div align="center">

| Input Type  | Status |
| :---------- | :----: |
| Pasted Text |    ✅   |
| Public URL  |    ✅   |
| PDF         |    ✅   |
| DOCX        |    ✅   |
| PPTX        |    ✅   |
| XLSX        |    ✅   |
| CSV         |    ✅   |
| PNG         |    ✅   |
| JPG / JPEG  |    ✅   |
| WEBP        |    ✅   |
| BMP         |    ✅   |
| TIFF        |    ✅   |
| GIF         |    ✅   |

</div>

---

# Document Processing

PrivacyLens AI uses different extraction methods depending on the input.

```text
PDF / DOCX / PPTX / XLSX / CSV
              ↓
       Native Extraction
              ↓
          Clean Text
```

For scanned or image-based content:

```text
Image / Scanned PDF
         ↓
      PyMuPDF
         ↓
   Tesseract OCR
         ↓
    Extracted Text
```

The extracted text then enters the same analysis pipeline.

---

# AI Layer

PrivacyLens AI uses **Groq** as its LLM provider.

```text
Extracted Document
        ↓
     Groq LLM
        ↓
   Fact Extraction
        ↓
Summary Generation
```

The LLM is mainly used for:

* Fact extraction
* Document summarization

Risk classification is kept separate from the LLM output.

---

# Tech Stack

<div align="center">

### Frontend

| Technology    | Purpose               |
| :------------ | :-------------------- |
| React         | User interface        |
| TypeScript    | Type-safe development |
| Vite          | Development & build   |
| React Router  | Routing               |
| Framer Motion | Animations            |
| Lucide React  | Icons                 |
| Recharts      | Visualizations        |

### Backend

| Technology | Purpose     |
| :--------- | :---------- |
| Python     | Backend     |
| FastAPI    | REST API    |
| Pydantic   | Validation  |
| Uvicorn    | ASGI server |

### Document & OCR

| Technology    | Purpose             |
| :------------ | :------------------ |
| PyPDF         | PDF text extraction |
| python-docx   | DOCX extraction     |
| python-pptx   | PPTX extraction     |
| openpyxl      | XLSX processing     |
| BeautifulSoup | HTML parsing        |
| HTTPX         | HTTP requests       |
| Pillow        | Image processing    |
| PyMuPDF       | PDF rendering       |
| Tesseract     | OCR                 |

### AI

| Technology | Purpose                         |
| :--------- | :------------------------------ |
| Groq       | Fact extraction & summarization |

</div>

---

# Project Structure

```text
PrivacyLensAI/
│
├── backend/
│   │
│   ├── api/
│   ├── models/
│   ├── processors/
│   ├── search/
│   ├── services/
│   ├── utils/
│   │
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   │
│   ├── src/
│   │   │
│   │   ├── components/
│   │   │   ├── conversation/
│   │   │   ├── layout/
│   │   │   ├── overlays/
│   │   │   └── ui/
│   │   │
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   │
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── README.md
```

---

# Prerequisites

Install these before running the project:

<div align="center">

| Requirement   | Needed                    |
| :------------ | :------------------------ |
| Python        | 3.10+                     |
| Node.js       | 20+                       |
| npm           | Included with Node.js     |
| Git           | Required                  |
| Tesseract OCR | Required for OCR          |
| Groq API Key  | Required for LLM features |

</div>

Check your environment:

```bash
python --version
node --version
npm --version
git --version
tesseract --version
```

---

# Setup

## 1. Clone the Repository

```bash
git clone https://github.com/Sayann18/PrivacyLens-AI.git
cd PrivacyLens-AI
```

---

## 2. Setup Backend

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment

Create:

```text
backend/.env
```

Add your configuration:

```env
LLM_ENABLED=true
LLM_PRIMARY_PROVIDER=groq

GROQ_ENABLED=true
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

TESSERACT_CMD=
```

Replace:

```text
your_groq_api_key
```

with your actual Groq API key.

---

## 4. Configure Tesseract

Tesseract is required for image and scanned-PDF OCR.

### Windows

If Tesseract is not available through PATH:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Verify:

```bash
tesseract --version
```

### Linux

```bash
sudo apt update
sudo apt install tesseract-ocr
```

Verify:

```bash
tesseract --version
```

---

## 5. Start the Backend

From `backend/`:

```bash
python -m uvicorn app:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Keep this terminal open.

---

## 6. Setup Frontend

Open a new terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Vite will display the local development URL.

Usually:

```text
http://localhost:5173
```

---

# Run Locally

You need two terminals.

### Terminal 1

```bash
cd backend
```

```bash
.venv\Scripts\activate
```

```bash
python -m uvicorn app:app --reload --port 8000
```

### Terminal 2

```bash
cd frontend
```

```bash
npm run dev
```

Then open the frontend URL shown by Vite.

---

# Application Flow

```text
                 Browser
                    │
                    ↓
             React Frontend
                    │
                 REST API
                    │
                    ↓
             FastAPI Backend
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    Extraction     OCR      Rule Engine
        │           │           │
        └───────────┼───────────┘
                    ↓
                 Groq LLM
                    │
                    ↓
              Evidence Check
                    │
                    ↓
               Final Result
```

---

# Quick Start

Already have Python, Node.js, Git, Tesseract, and your Groq API key?

### Backend

```bash
git clone https://github.com/Sayann18/PrivacyLens-AI.git
cd PrivacyLens-AI/backend

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

python -m uvicorn app:app --reload --port 8000
```

### Frontend

Open another terminal:

```bash
cd PrivacyLens-AI/frontend

npm install
npm run dev
```

---

# Environment Variables

Main backend configuration is stored in:

```text
backend/.env
```

Example:

```env
LLM_ENABLED=true
LLM_PRIMARY_PROVIDER=groq
GROQ_ENABLED=true
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
TESSERACT_CMD=
```

A complete configuration reference is available in:

```text
backend/.env.example
```

---

# Important Notes

### About the LLM

Groq is used for:

```text
Fact Extraction
Summary Generation
```

The rule-based engine handles the predefined clause detection and qualification logic.

### About OCR

Tesseract is used only when text needs to be extracted from:

```text
Images
Scanned PDFs
```

### About Results

PrivacyLens AI highlights potentially important conditions based on extracted content.

It does **not** determine legal enforceability.

---

# Limitations

* Results depend on the quality of extracted text.
* OCR accuracy depends on image quality.
* Complex legal language may require human review.
* PrivacyLens AI is an analysis tool, not legal advice.

---

# Future Improvements

```text
Voice Input
     ↓
Screenshot Analysis
     ↓
Improved Risk Visualization
     ↓
More Document Formats
     ↓
Advanced AI Agent Workflows
```

---

<div align="center">

# PrivacyLens AI

### Read less. Understand more.

Built by **Sayan Chakraborty**

</div>
