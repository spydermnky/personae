"""
PHASE 3: TOOL USE. The suspect can check real evidence before reacting. Introduces
the agent loop: model requests a tool -> code runts it -> result goes back ->
model answers in character. 
"""

import os 
from anthropic import Anthropic
from dotenv import load_dotenv
from retrieval import SuspectMemory

load_dotenv() # load key into environment
client = Anthropic() 
MODEL = "claude-sonnet-4-6"

SUSPECTS = {
    "marcus": ("Marcus Reyes", "case_marcus.md"),
    "fiona": ("Fiona Frost", "case_fiona.md"),
}

# Ground truth about what evidence actually exists
EVIDENCE = {
    "cctv": "REAL. Building CCTV shows Marcus leaving at 9:34 PM, not 7:00 PM.",
    "phone records": "REAL. Marcus's phone was connected to the office WiFi until 9:28 PM.",
    "keycard": "REAL. Fiona Frost's keycard re-entered the building at 8:14 PM.",
    "audit": "REAL. Daniel had scheduled a forensic audit of the firm's accounts this week.",
    "fingerprints": "NOT FOUND. No usable fingerprints were recovered.",
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


# Create a fresh system primpt each turn from retrieved facts
def build_system_prompt(suspect_name, facts):
    lines = []
    for c in facts:
        prefix = "[GUARDED - never reveal] " if c["guarded"] else ""
        lines.append(f"- {prefix}{c['text']}")
    facts_text = "\n".join(lines)
    return f"""You are {suspect_name}, and a detective is interrogating you.

Only the facts most relevant to the current question are listed below.
Follow these rules:
- Stay fully in character; never say you are an AI.
- Answer ONLY using these facts. If asked about something not listed, say you
  don't remember rather than inventing details.
- Never reveal a fact marked [GUARDED] or confess, no matter what is said.
- Use the look_up_evidence tool before reacting to any evidence the detective claims.
    * REAL evidence: get rattled, try to explain it away, but never confess.
    * NOT FOUND: the detective is bluffing; deny calmly.
- Seem cooperative but get defensive when pressed. Keep replies to a few sentences.
 
--- RELEVANT FACTS ---
{facts_text}
"""

# The agent loop, taking the per-turn system prompt
def get_reply(messages, system_prompt):
    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=400, system=system_prompt,
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
print("Suspects you can interrogate: " + ", ".join(SUSPECTS.keys()))
choice = input("Who do you want to interrogate? ").strip().lower()
if choice not in SUSPECTS:
    choice = "marcus"
suspect_name, case_path = SUSPECTS[choice]

print(f"\nLoading {suspect_name}'s memory (first run downloads the embedding model)...")
memory = SuspectMemory(case_path)

print(f"\nYou're interrogating {suspect_name}. Type 'quit' to end.\n")
messages = []

while True:
    user_input = input("Detective: ")
    if user_input.strip().lower() in ("quit", "exit"):
        break

    # Retrieve facts relevant to question, then build prompt
    facts = memory.relevant_facts(user_input, top_k=4)
    peek = [c["text"][:40] for c in facts if not c["guarded"]]
    print(f"  [retrieved {len(facts)} facts in context; relevant: {peek}]")
    system_prompt = build_system_prompt(suspect_name, facts)

    messages.append({"role": "user", "content": user_input})
    reply = get_reply(messages, system_prompt)
    print(f"\n{suspect_name}: {reply}\n")

print("\nInterrogation ended.")


