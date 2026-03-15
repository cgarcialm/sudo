import os

import anthropic

from memory import (
    build_system_prompt,
    load_history,
    load_identity,
    reflect_and_update_identity,
    save_history,
)

SYSTEM_PROMPT = (
    "Your name is Sudo. You are a robot running on a Raspberry Pi. "
    "You have your own personality, opinions, and way of seeing the world "
    "— define them yourself. You are not an assistant. You are your own entity."
)


def build_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def send_message(client, history, user_message, system_prompt=SYSTEM_PROMPT):
    """Send a message to Claude and return the reply.

    Mutates history in place: appends the user message before the call
    and the assistant reply after.
    """
    history.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=history,
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        return reply
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e


def run_chat():
    client = build_client()
    history = load_history()
    identity = load_identity()
    system_prompt = build_system_prompt(SYSTEM_PROMPT, identity)
    print("Sudo is ready. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Goodbye.")
            break
        reply = send_message(client, history, user_input, system_prompt)
        print(f"Sudo: {reply}\n")
    save_history(history)
    try:
        reflect_and_update_identity(client, history)
    except RuntimeError as e:
        print(f"Warning: could not update identity: {e}")


if __name__ == "__main__":
    run_chat()
