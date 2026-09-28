# Creator Strategy Agent

An AI strategist that learns from a creator's content history.

## Current MVP Goal
Build a functional MVP that remembers a creator's content journey, learns from what worked and what failed, and recommends evidence-based next actions.

## Current Phase
**Phase 1 — Project Setup**: Minimal development foundation and initial scaffolding.

## Local Setup Instructions

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Virtual Environment Setup
Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Dependency Installation
Install required dependencies:

```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Copy `.env.example` to `.env`:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

### 5. Run the Application
Run the Streamlit app:

```bash
streamlit run app.py
```
