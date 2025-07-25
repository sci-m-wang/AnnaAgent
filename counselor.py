from backbone import get_openai_client, model_name


def counsel(messages):
    client = get_openai_client()
    response = client.chat.completions.create(
        messages=messages,
        model=model_name,
    )
    return response.choices[0].message.content
