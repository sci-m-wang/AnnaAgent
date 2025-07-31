from .backbone import get_counselor_client
from .common.registry import registry


def counsel(messages):
    client = get_counselor_client()
    response = client.chat.completions.create(
        messages=messages,
        model=registry.get("anna_engine_config").counselor_model_name,
    )
    return response.choices[0].message.content
