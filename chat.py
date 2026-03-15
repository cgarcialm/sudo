import os

import anthropic

SYSTEM_PROMPT = "You are Sudo, a friendly AI robot assistant running on a Raspberry Pi."


def build_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def send_message(client, history, user_message):
    history.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        return reply
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e


def run_chat():
    client = build_client()
    history = []
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
        reply = send_message(client, history, user_input)
        print(f"Sudo: {reply}\n")


if __name__ == "__main__":
    run_chat()
