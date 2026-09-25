"""
Lesson 3: The Autonomous Loop (Your First True Agent with Self-Correction)
-------------------------------------------------------------------------
In Lesson 2, the AI called a single tool and stopped.
In this lesson, you build an AUTONOMOUS AGENT that:
  1. Tries an action (runs a broken script)
  2. Catches the error message
  3. Inspects the source code
  4. Fixes the bug by rewriting the file
  5. Verifies the fix by running it again!

This is the exact pattern behind coding agents like Cursor, Devin, and Copilot.
"""

import os
import subprocess
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
# STEP 1: Create a sample broken Python file to test our agent
# -------------------------------------------------------------
TARGET_FILE = "broken_math.py"

with open(TARGET_FILE, "w") as f:
    f.write('''# Intentional Buggy Script
def calculate_discounted_total(prices, discount_rate):
    # BUG: Typo in variable name (prices vs price_list) causes NameError!
    subtotal = sum(price_list)
    return subtotal * (1 - discount_rate)

cart = [25.0, 50.0, 100.0]
discount = 0.20
print("Total after discount:", calculate_discounted_total(cart, discount))
''')

print(f"📁 Created '{TARGET_FILE}' with an intentional bug.")


# -------------------------------------------------------------
# STEP 2: Define the Agent's Tools (Its "Hands")
# -------------------------------------------------------------

def run_python_script(filename: str) -> str:
    """
    Execute a python script and return its terminal output or error traceback.
    Args:
        filename: The path of the python file to run (e.g. 'broken_math.py').
    """
    print(f"\n⚙️  [ACTION] Running command: python {filename}...")
    result = subprocess.run(["python3", filename], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Script executed successfully!")
        return f"SUCCESS: Exit code 0.\nOutput:\n{result.stdout}"
    else:
        print("   ❌ Script failed! Passing traceback to agent...")
        return f"FAILURE: Exit code {result.returncode}.\nError Traceback:\n{result.stderr}"


def read_source_file(filename: str) -> str:
    """
    Read and return the complete source code of a file.
    Args:
        filename: The file path to read.
    """
    print(f"\n⚙️  [ACTION] Reading contents of {filename}...")
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_source_file(filename: str, new_content: str) -> str:
    """
    Overwrite a file with updated source code.
    Args:
        filename: The file to overwrite.
        new_content: The corrected Python code.
    """
    print(f"\n⚙️  [ACTION] Writing fixed code to {filename}...")
    try:
        with open(filename, "w") as f:
            f.write(new_content)
        return f"Successfully wrote new code to {filename}."
    except Exception as e:
        return f"Error writing file: {str(e)}"


# -------------------------------------------------------------
# STEP 3: Create the Autonomous Agent Session
# -------------------------------------------------------------
chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        tools=[run_python_script, read_source_file, write_source_file],
        system_instruction=(
            "You are an autonomous software debugging agent.\n"
            "Your workflow when fixing code:\n"
            "1. Run the script first to see the exact error.\n"
            "2. Read the source code to locate the bug.\n"
            "3. Write the corrected code to the file.\n"
            "4. Run the script again to VERIFY that it now passes with zero errors.\n"
            "Do not stop until the script runs cleanly!"
        )
    )
)

# -------------------------------------------------------------
# STEP 4: Give the Agent its Goal & Watch it Loop!
# -------------------------------------------------------------
goal = f"Make '{TARGET_FILE}' run cleanly without any errors."

print(f"\n🎯 AGENT GOAL: {goal}")
print("🤖 Starting the Autonomous Agent loop...\n" + "=" * 50)

response = chat.send_message(goal)

print("\n" + "=" * 50)
print("🏁 AGENT FINISHED:")
print("=" * 50)
print(response.text)
