"""
Kuber AI Gold Workflow - FastAPI single-file app
Filename: kuber_ai_gold_workflow.py

What this implements (assignment requirements):
- Two APIs that emulate a "Kuber AI" workflow for digital gold investment
  1) /gold-assistant: interacts like an LLM assistant, detects gold-related queries,
     returns facts, nudges user to invest and provides next step.
  2) /purchase-gold: executes a mock digital gold purchase, records transaction in SQLite DB

Features:
- SQLite database (file: data.db) created automatically with tables: users, purchases
- Simple LLM emulation via keyword detection + canned facts. Optional: there's a placeholder
  showing how to plug an actual LLM (OpenAI) by setting OPENAI_API_KEY env var.
- Hardcoded gold rate per gram (can be switched to a fetch-from-web function if desired).
- Endpoints to create user and fetch user profile.

How to run:
1. Install dependencies:
   pip install fastapi uvicorn pydantic

2. Run the server:
   uvicorn kuber_ai_gold_workflow:app --reload --port 8000

3. Use these endpoints (examples shown in README below):
   - POST /create-user           -> create a user
   - POST /gold-assistant       -> ask questions / get nudges
   - POST /purchase-gold        -> make a mock purchase
   - GET  /get-user/{user_id}   -> fetch user profile + purchases

Note: This file is intentionally single-file and well-commented to make it easy to
deploy and test locally or push to a hosting provider.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import Optional, Dict, Any, List
import os
import datetime

# --------------------------- Configuration ---------------------------
DB_FILE = "data.db"
# Hardcoded gold rate (INR per gram). Change as required or implement a fetch function.
GOLD_RATE_PER_GRAM = 6000.0

# If you want to integrate a real LLM: set OPENAI_API_KEY environment variable and
# implement the `call_llm()` function below. For the assignment demonstration,
# we use simple keyword detection + canned facts.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --------------------------- Database helpers ---------------------------

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # users: id, name, balance (INR), gold_grams (total held)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            balance REAL DEFAULT 0,
            gold_grams REAL DEFAULT 0
        )
        """
    )
    # purchases: id, user_id, amount_inr, grams, timestamp
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount_inr REAL NOT NULL,
            grams REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

# --------------------------- FastAPI + Models ---------------------------
app = FastAPI(title="Kuber AI Gold Workflow - Assignment Emulation")


class CreateUserRequest(BaseModel):
    name: str
    initial_deposit: Optional[float] = 0.0


class GoldAssistantRequest(BaseModel):
    user_id: int
    query: str


class PurchaseRequest(BaseModel):
    user_id: int
    amount_inr: float  # amount in INR user wants to spend


# --------------------------- Simple LLM Emulation ---------------------------

GOLD_KEYWORDS = [
    "gold",
    "digital gold",
    "invest in gold",
    "buy gold",
    "gold investment",
    "is gold safe",
    "should i buy gold",
]

CANNED_FACTS = (
    "Gold is traditionally considered a hedge against inflation and currency depreciation. "
    "It tends to preserve value over long periods, though short-term price movements can be volatile."
)


def query_is_about_gold(text: str) -> bool:
    text_lower = text.lower()
    for kw in GOLD_KEYWORDS:
        if kw in text_lower:
            return True
    return False


# Optional placeholder for real LLM call (e.g., OpenAI).
# If you set OPENAI_API_KEY in environment and want to use OpenAI, implement this.
# For now it's not used by default.

def call_llm(prompt: str) -> str:
    # SAMPLE: how you might call OpenAI's API (not implemented here)
    # import openai
    # openai.api_key = OPENAI_API_KEY
    # resp = openai.ChatCompletion.create(...)
    # return resp['choices'][0]['message']['content']
    return "(LLM placeholder) " + prompt


# --------------------------- Helper functions ---------------------------

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def update_user_gold_and_balance(user_id: int, grams: float, amount_inr: float):
    conn = get_conn()
    cur = conn.cursor()
    # decrement balance and increment gold_grams
    cur.execute(
        "UPDATE users SET balance = balance - ?, gold_grams = gold_grams + ? WHERE user_id = ?",
        (amount_inr, grams, user_id),
    )
    # insert purchase record
    cur.execute(
        "INSERT INTO purchases (user_id, amount_inr, grams, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, amount_inr, grams, datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_purchases_for_user(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE user_id = ? ORDER BY purchase_id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------------------- API Endpoints ---------------------------

@app.post("/create-user")
def create_user(req: CreateUserRequest):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, balance, gold_grams) VALUES (?, ?, ?)",
                (req.name, req.initial_deposit, 0.0))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "success", "user_id": user_id, "name": req.name, "balance": req.initial_deposit}


@app.get("/get-user/{user_id}")
def get_user_endpoint(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    purchases = get_purchases_for_user(user_id)
    return {"user": user, "purchases": purchases}


@app.post("/gold-assistant")
def gold_assistant(req: GoldAssistantRequest):
    # verify user exists
    user = get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # check if query is about gold
    is_gold = query_is_about_gold(req.query)

    if not is_gold:
        # If not about gold, optionally offer guidance
        response = (
            "I couldn't detect that your question is about gold investment. "
            "If you want to learn about gold investments, try asking 'Should I invest in gold?' or 'How to buy digital gold?'")
        return {"response": response, "is_gold_query": False}

    # If it is a gold-related question, prepare helpful facts + nudge
    # We use canned facts; you can replace with a real LLM call for richer answers.
    fact_answer = CANNED_FACTS
    nudge = (
        "If you'd like, I can help you invest in digital gold through the Simplify Money flow. "
        "A small test purchase (e.g., ₹10) is a great way to see how it works. Would you like to proceed?"
    )

    # Provide a structured response pointing to /purchase-gold for the next step.
    return {
        "response": fact_answer,
        "nudge": nudge,
        "next_step": "/purchase-gold",
        "is_gold_query": True,
    }


@app.post("/purchase-gold")
def purchase_gold(req: PurchaseRequest):
    # verify user exists
    user = get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.amount_inr <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # check balance
    if user["balance"] < req.amount_inr:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Available: {user['balance']}")

    # calculate grams using hardcoded rate
    grams = round(req.amount_inr / GOLD_RATE_PER_GRAM, 6)

    # update db
    update_user_gold_and_balance(req.user_id, grams, req.amount_inr)

    updated_user = get_user(req.user_id)
    purchases = get_purchases_for_user(req.user_id)

    return {
        "status": "success",
        "message": f"Successfully purchased gold worth ₹{req.amount_inr} ({grams} g) for user_id: {req.user_id}",
        "purchase": {"amount_inr": req.amount_inr, "grams": grams},
        "updated_profile": updated_user,
        "purchases": purchases,
    }


# --------------------------- Extra: simple health route ---------------------------
@app.get("/")
def root():
    return {"message": "Kuber AI Gold Workflow API running. See /docs for Swagger UI."}


# --------------------------- End of file ---------------------------
