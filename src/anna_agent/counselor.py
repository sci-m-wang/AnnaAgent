from .backbone import get_counselor_client, model_name


def counsel(messages):
    client = get_counselor_client()
    response = client.chat.completions.create(
        messages=messages,
        model=model_name,
    )
    return response.choices[0].message.content
