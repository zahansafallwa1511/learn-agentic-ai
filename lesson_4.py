"""
Lesson 4: Memory & Knowledge (Remembering Context & Plain-English RAG)
---------------------------------------------------------------------
In this lesson, you solve the two biggest limitations of AI:
  1. AMNESIA: When your program restarts, the AI forgets everything.
     -> SOLUTION: Long-term memory backed by a persistent SQLite database.
  2. LIMITED KNOWLEDGE: The AI doesn't know your private company handbook.
     -> SOLUTION: RAG (Retrieval-Augmented Generation) — a tool that searches
        documents and pulls the right paragraphs into context on demand.
"""

import os
import json
import sqlite3
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
# PART 1: The Long-Term Memory Store (Persistent SQLite Database)
# -------------------------------------------------------------
DB_FILE = "agent_memory.db"

# Initialize our SQLite database table
with sqlite3.connect(DB_FILE) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_memories (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def save_memory(fact_key: str, fact_value: str) -> str:
    """
    Save an important user preference, role, or factual note into persistent memory.
    Args:
        fact_key: Short identifier for the memory (e.g. 'user_name', 'user_title', 'preferred_coffee').
        fact_value: The detail to remember (e.g. 'Sarah', 'VP of Engineering').
    """
    print(f"\n🧠 [MEMORY WRITE] Saving to SQLite: {fact_key} = '{fact_value}'")
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_memories (key, value) VALUES (?, ?)",
            (fact_key, fact_value)
        )
        conn.commit()
    return f"Successfully saved memory: {fact_key} = {fact_value}"


def recall_memories() -> str:
    """
    Retrieve all facts and preferences stored in the user's persistent long-term memory.
    """
    print("\n🧠 [MEMORY READ] Querying SQLite for saved memories...")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT key, value FROM user_memories")
        rows = cursor.fetchall()
    
    if not rows:
        return "No long-term memories found."
    return json.dumps(dict(rows))


# -------------------------------------------------------------
# PART 2: Private Company Knowledge Base (RAG in Plain English!)
# -------------------------------------------------------------
COMPANY_KNOWLEDGE_BASE = {
    "deployment_guide.md": (
        "Production deployments take place every Thursday at 3:00 PM. "
        "Any deployment outside this window is considered an emergency release. "
        "Emergency releases must be authorized by the VP of Engineering and "
        "broadcasted in the #incident-war-room Slack channel."
    ),
    "refund_policy.md": (
        "Standard customers may request refunds within 14 days of purchase. "
        "Enterprise tier clients have a 60-day money-back guarantee with zero cancellation fees."
    ),
    "office_perks.md": (
        "Full-time employees receive a $100/month learning stipend and free gym membership."
    )
}


def search_company_docs(search_query: str) -> str:
    """
    Search company handbook and policy documents for relevant sections.
    Args:
        search_query: The keywords or question to search for (e.g. 'emergency release', 'refund policy').
    """
    print(f"\n🔍 [RAG SEARCH] Searching internal docs for: '{search_query}'...")
    query_words = search_query.lower().split()
    matched_sections = []
    
    for filename, content in COMPANY_KNOWLEDGE_BASE.items():
        # Simple, fast keyword match (the essence of document retrieval):
        if any(word in content.lower() for word in query_words if len(word) > 3):
            matched_sections.append(f"--- Document: {filename} ---\n{content}")
            
    if not matched_sections:
        return f"No documents matched your search: '{search_query}'"
    return "\n\n".join(matched_sections)


# Registry of tools available to our agent
TOOL_REGISTRY = {
    "save_memory": save_memory,
    "recall_memories": recall_memories,
    "search_company_docs": search_company_docs
}


# -------------------------------------------------------------
# PART 3: The Explicit ReAct Loop Function
# -------------------------------------------------------------
def run_agent_session(session_name: str, user_prompt: str):
    """Runs a fresh agent conversation with our explicit while loop."""
    print("\n" + "=" * 65)
    print(f"🚀 STARTING {session_name}")
    print(f"👤 User: '{user_prompt}'")
    print("=" * 65)
    
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        config=types.GenerateContentConfig(
            tools=list(TOOL_REGISTRY.values()),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            system_instruction=(
                "You are an Executive AI Assistant.\n"
                "You have access to:\n"
                "1. A persistent long-term memory database (SQLite) for user facts.\n"
                "2. A private company documentation search tool (RAG).\n"
                "When asked who the user is or what their preferences are, check memories first.\n"
                "When asked about company rules or policies, search the company docs.\n"
                "Always combine personal memory with company policies to provide tailored answers."
            )
        )
    )
    
    current_input = user_prompt
    step = 1
    MAX_STEPS = 6
    
    while step <= MAX_STEPS:
        response = chat.send_message(current_input)
        
        if response.function_calls:
            tool_responses = []
            for call in response.function_calls:
                func_name = call.name
                func_args = call.args
                print(f"  🤖 Agent Action: `{func_name}`({func_args})")
                
                # Execute Python tool
                fn = TOOL_REGISTRY.get(func_name)
                output = fn(**func_args) if fn else "Tool not found"
                
                tool_responses.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": output}
                    )
                )
            current_input = tool_responses
        else:
            print(f"\n🏁 {session_name} Finished:")
            print(response.text)
            break
        step += 1


# -------------------------------------------------------------
# PART 4: Demonstration of 2 Separate Sessions Across Time
# -------------------------------------------------------------
if __name__ == "__main__":
    # SESSION 1: The user introduces herself and shares key facts.
    # Notice: The agent saves this to the SQLite database on your hard drive!
    run_agent_session(
        session_name="SESSION 1 (First Interaction)",
        user_prompt="Hi! My name is Sarah, and I am the VP of Engineering. Please remember this."
    )

    # SESSION 2: Pretend this is the next day. The Python chat memory is completely reset!
    # The agent must recall from SQLite to know who she is, and search RAG docs to know the policy.
    run_agent_session(
        session_name="SESSION 2 (The Next Day - Fresh Session)",
        user_prompt="Who am I, and what is our procedure if we need to do an emergency release?"
    )
