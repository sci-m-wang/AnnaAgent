from openai import OpenAI

def counsel(messages):
    client = OpenAI(
        api_key="counselor",
        base_url="http://0.0.0.0:8002/v1"
    )

    response = client.chat.completions.create(
        messages=messages,
        model="counselor"
    )

    return response.choices[0].message.content
