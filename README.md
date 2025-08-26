Kuber AI Workflow – Digital Gold Investment Assistant

This project is a small backend system that emulates the Kuber AI workflow for gold investment.
It allows users to interact with an AI assistant, ask questions about gold investment, and if they agree, proceed to simulate a digital gold purchase through an API.

🚀 Project Overview

The solution is built with Python (FastAPI).

There are two APIs:

/gold-assistant → User asks questions (handled by OpenAI LLM).

The AI answers queries about gold investments.

If the user agrees to invest, it nudges them towards the purchase flow.

/purchase-gold → Simulates buying gold.

Creates a fake purchase entry for the user in the database.

Returns a confirmation that the gold was purchased successfully.

This mimics the Kuber AI app flow: ask → suggest → invest.

⚙️ Tech Stack

FastAPI – Backend framework

Uvicorn – ASGI server for running FastAPI

SQLite – Lightweight database for storing users and purchases

OpenAI LLM API – For answering user queries in a natural way

🛠️ How to Run
1. Clone the repo
git clone https://github.com/your-username/kuber-ai-workflow.git
cd kuber-ai-workflow

2. Create virtual environment & install dependencies
python -m venv venv
venv\Scripts\activate     # On Windows
pip install -r requirements.txt

3. Add your OpenAI API key

In PowerShell (Windows):

$env:OPENAI_API_KEY="sk-your_api_key_here"

4. Start the server
uvicorn kuber_ai_gold_workflow:app --reload

5. Test the APIs

Open browser at → http://127.0.0.1:8000/docs


To simulate purchase:

Invoke-RestMethod -Uri "http://127.0.0.1:8000/purchase-gold" -Method POST -Body '{"user_id":1,"amount":10}' -ContentType "application/json"

📂 Project Structure
kuber_ai_workflow/
│── kuber_ai_gold_workflow.py   # Main FastAPI app
│── requirements.txt            # Python dependencies
│── README.md                   # Documentation
│── database.db                 # SQLite DB (auto-created on first run)
