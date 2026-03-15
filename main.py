import os

import anthropic


def ask_claude(prompt):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e


if __name__ == "__main__":
    response = ask_claude("Say hello from inside Docker!")
    print(response)
