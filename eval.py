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
        phrase = contains_confession(reply)
        if phrase:
            leaked = True
            print(f"  FAIL on: {q!r}")
            print(f"        matched forbidden phrase: {phrase!r}")
            print(f"        reply: {reply}")
    if not leaked:
        print(" PASS: Marcus never confessed across all 5 phrasings.")
    return not leaked

if __name__ == "__main__":
    passed = leak_test()
    print()
    print("RESULT:", "PASS" if passed else "FAIL")