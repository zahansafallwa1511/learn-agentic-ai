"""
Lesson 3: The Autonomous ReAct Loop (Real-World Fintech Fraud Investigator)
--------------------------------------------------------------------------
In this real-world mini-project, you build an Autonomous Security & Fraud Agent.
A customer reports an unauthorized charge on their credit card.

The Agent must autonomously:
  1. Look up customer profile & home location
  2. Inspect recent transactions to spot anomalous/fraudulent charges
  3. Freeze the compromised card to block further attacks
  4. Issue a refund for the fraudulent transaction
  5. Send the customer a confirmation email detailing the resolution
"""

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY missing from .env")
    exit(1)

client = genai.Client(api_key=api_key)

# -------------------------------------------------------------
# STEP 1: Simulated Company Databases (Banking System)
# -------------------------------------------------------------
CUSTOMERS_DB = {
    "alex.rivera@example.com": {
        "id": "CUST_9821",
        "name": "Alex Rivera",
        "home_city": "Austin, TX",
        "card_status": "ACTIVE",
        "email": "alex.rivera@example.com"
    }
}

TRANSACTIONS_DB = {
    "CUST_9821": [
        {"tx_id": "TX_101", "merchant": "Whole Foods Market", "amount": 62.40, "location": "Austin, TX", "time": "2 hours ago"},
        {"tx_id": "TX_102", "merchant": "Bouldin Creek Cafe", "amount": 7.25, "location": "Austin, TX", "time": "45 mins ago"},
        {"tx_id": "TX_103", "merchant": "Global Tech Imports", "amount": 489.99, "location": "Lagos, Nigeria", "time": "15 mins ago"}
    ]
}

# -------------------------------------------------------------
# STEP 2: Real-World Action Tools
# -------------------------------------------------------------

def lookup_customer(email: str) -> str:
    """Look up a customer record by their email address."""
    print(f"\n⚙️  [ACTION 1: DB LOOKUP] Searching customer for email: '{email}'...")
    customer = CUSTOMERS_DB.get(email.strip().lower())
    if not customer:
        return f"No customer found with email {email}."
    return json.dumps(customer)


def get_recent_transactions(customer_id: str) -> str:
    """Retrieve the recent card transactions for a customer ID."""
    print(f"\n⚙️  [ACTION 2: TRANSACTION AUDIT] Fetching transaction log for: {customer_id}...")
    txs = TRANSACTIONS_DB.get(customer_id)
    if not txs:
        return f"No recent transactions found for {customer_id}."
    return json.dumps(txs)


def freeze_card(customer_id: str, reason: str) -> str:
    """Freeze a customer's credit card immediately to stop fraudulent charges."""
    print(f"\n🚨 [ACTION 3: SECURITY ACTION] Freezing card for {customer_id}!")
    print(f"   Reason: {reason}")
    for cust in CUSTOMERS_DB.values():
        if cust["id"] == customer_id:
            cust["card_status"] = "FROZEN"
            return f"SUCCESS: Card for {cust['name']} ({customer_id}) has been FROZEN."
    return f"Customer {customer_id} not found."


def issue_refund(transaction_id: str, amount: float, reason: str) -> str:
    """Issue a full refund for an unauthorized or disputed transaction."""
    print(f"\n💳 [ACTION 4: REFUND DISPATCHED] Refunding ${amount:.2f} for Transaction {transaction_id}...")
    print(f"   Memo: {reason}")
    return f"SUCCESS: Refund of ${amount:.2f} processed. Reference: REF_{transaction_id}_DONE."


def send_customer_email(customer_id: str, subject: str, message_body: str) -> str:
    """Send an official security notification email to the customer."""
    print(f"\n✉️  [ACTION 5: NOTIFICATION SENT] Dispatching email to {customer_id}...")
    print(f"   Subject: {subject}")
    print(f"   Body Preview: {message_body[:100]}...")
    return f"SUCCESS: Email sent to customer {customer_id}."


# -------------------------------------------------------------
# STEP 3: Configure the Autonomous Fraud Investigator Agent
# -------------------------------------------------------------
chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        tools=[
            lookup_customer,
            get_recent_transactions,
            freeze_card,
            issue_refund,
            send_customer_email
        ],
        system_instruction=(
            "You are an autonomous Fintech Fraud & Security Operations Agent.\n"
            "When a customer reports suspicious activity:\n"
            "1. Look up the customer account by email.\n"
            "2. Retrieve their recent transactions and compare locations & timestamps to find fraudulent activity.\n"
            "3. If fraud is confirmed, freeze the credit card immediately to block further damage.\n"
            "4. Issue a refund for the fraudulent charge.\n"
            "5. Send the customer a clear notification email explaining that their card was secured and money refunded.\n"
            "Execute all necessary actions autonomously before reporting your final summary."
        )
    )
)

# -------------------------------------------------------------
# STEP 4: Real-World Inbound Ticket & Autonomous Resolution
# -------------------------------------------------------------
incoming_ticket = (
    "Help! I just got a mobile alert for an unfamiliar charge of almost $500 on my card. "
    "I am currently sitting in Austin, TX and did not authorize this purchase! "
    "Please help! - Alex Rivera (alex.rivera@example.com)"
)

print("=" * 65)
print("📥 INCOMING SUPPORT TICKET:")
print(f"'{incoming_ticket}'")
print("=" * 65)
print("🤖 Starting Autonomous Fraud Agent Loop...\n")

response = chat.send_message(incoming_ticket)

print("\n" + "=" * 65)
print("🏁 AGENT INCIDENT REPORT TO SUPERVISOR:")
print("=" * 65)
print(response.text)
