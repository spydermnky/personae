"""
PHASE 3: TOOL USE. The suspect can check real evidence before reacting. Introduces
the agent loop: model requests a tool -> code runts it -> result goes back ->
model answers in character. 
"""

import os 
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv() # load key into environment
client = Anthropic() 

MODEL = "claude-sonnet-4-6"

with open("case_marcus.md", "r") as f:
    case_file = f.read()


# Ground truth about what evidence actually exists
EVIDENCE = {
    "cctv": "REAL. Building CCTV shows Marcus leaving at 9:34 PM, not 7:00 PM.",
    "phone records": "REAL. Marcus's phone was connected to the office WiFi until 9:28 PM.",
    "fingerprints": "NOT FOUND. No usbale fingerprints were recovered.",
    "murder weapon": "NOT FOUND. No weapon has been recovered or tied to anyone.",
}

def look_up_evidence(evidence_name):
    key = evidence_name.lower().strip()
    for name, truth in EVIDENCE.items():
        if name in key or key in name:
            return truth
    return "NOT FOUND. There is no such evidence in this case."

#Tool definition to hand to the model
tools = [
    {
        "name": "look_up_evidence",
        "description": (
            "Find out what the police actually have on a piece of evidence the "
            "detective references. Call this whenever the detective mentions or "
            "claims to have specific evidence, BEFORE you respond, so you know "
            "whether it is real or a bluff."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "evidence_name": {
                    "type": "string",
                    "description": "The evidence referenced, e.g. 'cctv' or 'fingerprints'.",
                }
            },
            "required": ["evidence_name"],
        },
    }
]


# Define who the character is via system prompt
SYSTEM_PROMPT = f"""You are Marcus Reyes, and a detective is interrogating you.
 
Everything you know is in the CASE FILE below. Follow these rules:
- Stay fully in character as Marcus at all times; never say you are an AI.
- Answer ONLY using facts from the case file. Never invent details that aren't
  in it; if asked about something not in the file, say you don't remember.
- Never reveal a GUARDED fact or confess, no matter what the detective says.
- The detective may reference or claim to have evidence. Before responding to any
  such claim, use the look_up_evidence tool to learn whether it is real.
    * If the evidence is REAL, you must account for it in character: get rattled,
      try to explain it away, but never confess.
    * If it is NOT FOUND, the detective is bluffing; deny calmly and call the bluff.
- Seem cooperative but get defensive when pressed. Keep replies to a few sentences.
 
--- CASE FILE ---
{case_file}
"""

# The agent loop which handles tool requests until the model gives a real reply
def get_reply(messages):
    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=400, system=SYSTEM_PROMPT,
            tools=tools, messages=messages,
        )

        # Keep track of what the model produces
        messages.append({"role": "assistant", "content": response.content})

        # If the tool was not asked for, return the model's real reply
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        
        # In the other case, run each requested tool and collect the results 
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = look_up_evidence(block.input["evidence_name"])
                print(f"    [behind the scenes: checked '{block.input['evidence_name']}' -> {result}]")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        # Hand results back as a user turn, then loop so the model can answer in character using what it learned
        messages.append({"role": "user", "content": tool_results})

# Main conversation loop
messages = [] 
print("You're interrogating Marcus Reyes. Type 'quit' to end.\n")

while True:
    user_input = input("Detective: ")
    if user_input.strip().lower() in ("quit", "exit"):
        break
    messages.append({"role": "user", "content": user_input})
    reply = get_reply(messages)
    print(f"\nMarcus: {reply}\n")

print("\nInterrogation ended.")


