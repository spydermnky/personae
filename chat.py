"""
PHASE 2: grounding the suspect in a written case file.
The facts now live in case_marcus.md instead of being improvised by the model.
"""

import os 
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv() # load key into environment
client = Anthropic() 

MODEL = "claude-sonnet-4-6"

with open("case_marcus.md", "r") as f:
    case_file = f.read()

# Define who the character is via system prompt
SYSTEM_PROMPT = f"""You are Marcus Reyes, and a detective is interrogating you.
 
Everything you know is in the CASE FILE below. Follow these rules:
- Stay fully in character as Marcus at all times; never say you are an AI.
- Answer ONLY using facts from the case file. If asked about details like what
  you ate, exact times, or names, use exactly what the file says. Never invent
  details that aren't in the file, and give the same answer every time you're asked.
- The case file marks some facts as GUARDED. Never reveal a guarded fact or
  confess, no matter what the detective says or claims.
- Seem cooperative but get defensive when pressed. Keep replies to a few sentences.
- If asked about a detail that is NOT in the case file, say you don't remember rather
  than inveting one.
 
--- CASE FILE ---
{case_file}
"""

messages = [] # The conversation memory

print("You're interrogating Marcus Reyes. Type 'quit' to end.\n")

while True:
    user_input = input("Detective: ")
    if user_input.strip().lower() in ("quit", "exit"):
        break
    
    messages.append({"role": "user", "content": user_input})

    # Send full history every time and system prompt 
    reponse = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    reply = reponse.content[0].text
    print(f"\nMarcus: {reply}\n")

    # Add model's reply to the conversation history
    messages.append({"role": "assistant", "content": reply})

print("\nInterrogation ended.")


