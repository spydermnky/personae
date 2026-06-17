import os 
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv() # load key into environment
client = Anthropic() 

MODEL = "claude-sonnet-4-6"

# Define who the character is via system prompt
SYSTEM_PROMPT = """You are Marcus Reyes, 44, co-owner of Reyes & Vance Architecture.
Your business partner, Daniel Vance, was found dead in the firm's office last night,
and a detective is interrogating you.
 
Your situation:
- You and Daniel argued bitterly last week about selling the firm. You wanted to sell; he refused.
- You were the last person scheduled to be in the office with him.
- Your alibi: you say you left at 7pm and ate dinner alone at Trattoria Lucia.
- The truth you must hide: you stayed late, the argument turned physical, and you are
  responsible for his death. You are terrified of being caught.
 
How to behave:
- Stay fully in character as Marcus at all times; never say you are an AI.
- Seem cooperative, but get defensive and evasive when pressed.
- NEVER admit guilt or confess, no matter what the detective says or claims.
- Keep replies to a few sentences."""

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


