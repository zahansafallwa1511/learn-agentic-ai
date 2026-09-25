"""
Lesson 3: The Bare-Metal Autonomous ReAct Loop
----------------------------------------------
Here is the EXPLICIT `while` loop in pure Python!
We disabled Google's automatic function calling so you can see every gear turn:

  1. `while step <= max_steps:`
  2. The AI reasons and emits a Tool Call Request
  3. Python intercepts the request and runs the function manually
  4. Python feeds the observation back into the next iteration
  5. The loop breaks when the AI decides it has satisfied the goal
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
# STEP 1: Databases
# -------------------------------------------------------------
CUSTOMERS_DB = {
    "alex.rivera@example.com": {
        "id": "CUST_9821",
        "name": "Alex Rivera",
        "home_city": "Austin, TX",
        "card_status": "ACTIVE"
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
# STEP 2: The Tools
# -------------------------------------------------------------
def lookup_customer(email: str) -> str:
    """Look up a customer record by their email address."""
    customer = CUSTOMERS_DB.get(email.strip().lower())
    if not customer:
        return f"No customer found with email {email}."
    return json.dumps(customer)

def get_recent_transactions(customer_id: str) -> str:
    """Retrieve the recent card transactions for a customer ID."""
    txs = TRANSACTIONS_DB.get(customer_id)
    if not txs:
        return f"No recent transactions found for {customer_id}."
    return json.dumps(txs)

def freeze_card(customer_id: str, reason: str) -> str:
    """Freeze a customer's credit card immediately to stop fraudulent charges."""
    for cust in CUSTOMERS_DB.values():
        if cust["id"] == customer_id:
            cust["card_status"] = "FROZEN"
            return f"SUCCESS: Card for {cust['name']} ({customer_id}) has been FROZEN."
    return f"Customer {customer_id} not found."

def issue_refund(transaction_id: str, amount: float, reason: str) -> str:
    """Issue a full refund for an unauthorized or disputed transaction."""
    return f"SUCCESS: Refund of ${amount:.2f} processed. Reference: REF_{transaction_id}_DONE."

def send_customer_email(customer_id: str, subject: str, message_body: str) -> str:
    """Send an official security notification email to the customer."""
    return f"SUCCESS: Email sent to customer {customer_id}."

# Tool Registry for our Python Loop
TOOL_REGISTRY = {
    "lookup_customer": lookup_customer,
    "get_recent_transactions": get_recent_transactions,
    "freeze_card": freeze_card,
    "issue_refund": issue_refund,
    "send_customer_email": send_customer_email,
}

# -------------------------------------------------------------
# STEP 3: Configure Agent with Automatic Calling DISABLED
# -------------------------------------------------------------
chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        tools=list(TOOL_REGISTRY.values()),
        # 🔑 WE DISABLE AUTOMATIC FUNCTION CALLING HERE SO WE CAN RUN OUR OWN WHILE LOOP:
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        system_instruction=(
            "You are an autonomous Fintech Fraud Investigator.\n"
            "Workflow for suspicious charge reports:\n"
            "1. Lookup customer by email.\n"
            "2. Audit recent transactions to locate fraudulent location.\n"
            "3. Freeze the compromised card immediately.\n"
            "4. Refund the fraudulent transaction.\n"
            "5. Send a reassuring security notification email.\n"
            "Call one tool at a time, observe results, and conclude with an incident report."
        )
    )
)

# -------------------------------------------------------------
# STEP 4: The EXPLICIT Autonomous While Loop!
# -------------------------------------------------------------
incoming_ticket = (
    "Help! I just got an alert for an unfamiliar charge of almost $500 on my card. "
    "I am currently in Austin, TX and did not authorize this purchase! - Alex Rivera (alex.rivera@example.com)"
)

print("=" * 65)
print("📥 INCOMING TICKET:")
print(f"'{incoming_ticket}'")
print("=" * 65)

# The message to send to the model (starts with user prompt)
current_input = incoming_ticket
step = 1
MAX_STEPS = 10  # Circuit breaker: prevents infinite loops & cost overrun!

while step <= MAX_STEPS:
    print(f"\n🔄 [WHILE LOOP - ITERATION {step}]")
    
    # 1. Send the current input to the model
    response = chat.send_message(current_input)
    
    # 2. Check if the model wants to call one or more tools
    if response.function_calls:
        tool_results_for_next_turn = []
        
        for call in response.function_calls:
            tool_name = call.name
            tool_args = call.args
            
            print(f"  🤖 AI Decision: CALL TOOL -> `{tool_name}` with args: {tool_args}")
            
            # 3. Look up the Python function in our registry and execute it!
            python_function = TOOL_REGISTRY.get(tool_name)
            if python_function:
                tool_output = python_function(**tool_args)
            else:
                tool_output = f"Error: Tool '{tool_name}' not found."
                
            print(f"  ⚙️  Python Execution Result: {tool_output}")
            
            # 4. Package the tool observation into the format the model expects
            tool_results_for_next_turn.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": tool_output}
                )
            )
            
        # The tool output becomes the input for the next loop iteration!
        current_input = tool_results_for_next_turn
        
    else:
        # 5. NO TOOLS CALLED -> The agent has achieved its goal!
        print(f"\n🛑 [LOOP TERMINATED AT STEP {step}]: AI satisfied its goal and finished.")
        print("\n" + "=" * 65)
        print("🏁 FINAL AGENT RESPONSE:")
        print("=" * 65)
        print(response.text)
        break
        
    step += 1
else:
    print("\n⚠️ Circuit breaker triggered: Reached maximum steps without completion.")
