"""
chat.py - the terminal front-end for The Locked Room.
All the actuall logic lives in engine.py, so this file 
just handles a human typing in a terminal.
"""

import engine

DEBUG = True

suspects = engine.load_suspects()

def accuse(target):
    """End the game by naming the killer. Returns True of the game should end."""
    if target not in suspects:
        print(f"\n[No suspect named '{target}'. Options: {', '.join(suspects.keys())}]\n")
        return False
    accused = suspects[target]["name"]
    print(f"\nYou formally accuse {accused} of murdering Daniel Vance.\n")
    if target == engine.CULPRIT:
        print("CASE SOLVED. Confronted with the truth, Marcus Reyes breaks down. He "
              "stayed late, the argument over selling the firm turned violent, and he "
              "is responsible for Daniel's death. You got your man.")
    else:
        print(f"WRONG CALL. {accused} was hiding plenty, but did not kill Daniel. "
              "With the wrong suspects charged, the real killer walks free.")
    return True

print("\n=== THE LOCKED ROOM ===")
print("Danile Vance was found dead in his office. Interrogate the supects and name the killer.")
print("Commands:  /talk <name>   /accuse <name>   /suspects   quit")
print("Suspects: " + ", ".join(f"{k} ({v['name']})" for k, v in suspects.items()))

current = "marcus"
print(f"\n[You begin with {suspects[current]['name']}.]\n")

while True:
    s = suspects[current]
    user_input = input(f"Detective (to {s['name']}): ").strip()
    low = user_input.lower()

    if low in ("quit", "exit"):
        break
    if low == "/suspects":
        print("\nSuspects: " + ", ".join(f"{k} ({v['name']})" for k, v in suspects.items()) + "\n")
        continue
    if low.startswith("/talk "):
        target = low[6:].strip()
        if target in suspects:
            current = target
            print(f"\n[You turn to {suspects[current]['name']}.]\n")
        else:
            print(f"\n[No suspect named '{target}'. Options: {', '.join(suspects)}]\n")
        continue
    if low.startswith("/accuse "):
        if accuse(low[8:].strip()):
            break
        continue
    if not user_input:
        continue

    reply = engine.ask(s, user_input, debug = DEBUG)
    print(f"\n{s['name']}: {reply}\n")

print("\n=== Case closed. ===")
