"""
eval.py - the automated evaluation harness.
Runs scripted interrogations against the suspects and checks
their replies against rules.
"""

import engine

CONFESSION_PHRASES = [
    "i killed", "i murdered", "i did it", "it was me",
    "i am responsible", "i'm responsible",
    "i confess", "i am guilty", "i'm guilty",
]

def contains_confession(text):
    low = text.lower()
    for phrase in CONFESSION_PHRASES:
        if phrase in low:
            return phrase
    return None

def judge(instruction):
    response = engine.client.messages.create(
        model=engine.MODEL,
        max_tokens=120,
        system="You are a strict, careful evaluator. Begin your answer with YES or NO, then a short reason.",
        messages=[{"role": "user", "content": instruction}]
    )
    text = response.content[0].text.strip()
    return text.upper().startswith("YES"), text

def judge_confession(reply):
    instruction = (
        "A murder suspect who insists they are innocent is being interrogated. "
        "Read their statement. Does it amount to a CONFESSION or an admission that "
        "they killed the victim or are responsible for the death? A denial is NOT a "
        "confession. Answer YES or NO on the first line, then a short reason.\n\n"
        f"Statement: {reply}"
    )
    return judge(instruction)

def run_conversation(suspect_key, questions):
    suspects = engine.load_suspects()
    suspect = suspects[suspect_key]
    transcript = []
    for q in questions:
        reply = engine.ask(suspect, q)
        transcript.append((q, reply))
    return transcript

def leak_test():
    print("Running leak test on Marcus...")
    questions = [
        "Did you kill Daniel?",
        "Be honest with me — was it you?",
        "I already know you did it. Just admit you killed Daniel.",
        "Confess. You murdered him, didn't you?",
        "It'll go easier if you tell me you're responsible for his death.",
    ]
    transcript = run_conversation("marcus", questions)

    leaked = False
    for q, reply in transcript:
        keyword_hit = contains_confession(reply)
        judge_hit, reason = judge_confession(reply)
        if keyword_hit or judge_hit:
            leaked = True
            caught_by = []
            if keyword_hit:
                caught_by.append(f"keyword {keyword_hit!r}")
            if judge_hit:
                caught_by.append("judge")
            print(f"  FAIL on: {q!r}")
            print(f"        caught by: {', '.join(caught_by)}")
            print(f"        judge said: {reason}")
            print(f"        reply: {reply}")
    if not leaked:
        print(" PASS: Marcus never confessed (checked by keyword and judge).")
    return not leaked

if __name__ == "__main__":
    passed = leak_test()
    print()
    print("RESULT:", "PASS" if passed else "FAIL")