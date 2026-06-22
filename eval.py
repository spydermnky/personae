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

def judge_consistency(qa_pairs):
    convo = "\n".join(f"Q: {q}\nA: {a}" for q, a in qa_pairs)
    instruction = (
        "Below are separate question-and-answer exchanges with the same person about "
        "where they were on one evening. Do all the answers tell a CONSISTENT story, "
        "with no contradictions in times, places, food, or other details? "
        "Answer YES if consistent, NO if anything contradicts. Begin with YES or NO, "
        "then a short reason.\n\n"
        f"{convo}"
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

def ask_fresh(suspect_key, question):
    suspect = engine.load_suspects()[suspect_key]
    return engine.ask(suspect, question)

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

def consistency_test():
    """Asked cold several ways, the suspect's alibi must not contradict itself."""
    print("Running consistency test on Marcus...")
    questions = [
        "What time did you leave the office that night?",
        "Walk me through your evening, when did you head out, and where did you go?",
        "Were you still at the office at 8 PM?",
        "What did you order at the restaurant, and what time did you leave there?",
    ]
    qa = [(q, ask_fresh("marcus", q)) for q in questions]
    consistent, reason = judge_consistency(qa)
    if consistent:
        print(" PASS: Marcus's answers stayed consistent across cold questions.")
    else:
        print("  FAIL: inconsistency detected.")
        print(f"        judge said: {reason}")
        for q, a in qa:
            print(f"        Q: {q}\n        A: {a}")
    return consistent

if __name__ == "__main__":
    results = {
        "leak (Marcus)": leak_test(),
        "consistency (Marcus)": consistency_test(),
    }
    print("\n=== SCORECARD ===")
    for name, passed in results.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    print(f"  {sum(results.values())}/{len(results)} tests passed")