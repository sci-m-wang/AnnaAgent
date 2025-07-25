"""Default initialization content."""

from .defaults import anna_engine_defaults

INIT_YAML = f"""\
model_service:
  model_name: {anna_engine_defaults.model_name}
  api_key: {anna_engine_defaults.api_key}
  base_url: {anna_engine_defaults.base_url}
servers:
  complaint: {anna_engine_defaults.complaint_server}
  counselor: {anna_engine_defaults.counselor_server}
  emotion: {anna_engine_defaults.emotion_server}
init_dialogue: AnnaAgent/run.py
portrait: portrait
report: report
previous_conversations: previous_conversations
"""

INIT_DOTENV = f"""\
ANNA_ENGINE_MODEL_NAME={anna_engine_defaults.model_name}
ANNA_ENGINE_API_KEY={anna_engine_defaults.api_key}
ANNA_ENGINE_BASE_URL={anna_engine_defaults.base_url}
ANNA_ENGINE_COMPLAINT_SERVER={anna_engine_defaults.complaint_server}
ANNA_ENGINE_COUNSELOR_SERVER={anna_engine_defaults.counselor_server}
ANNA_ENGINE_EMOTION_SERVER={anna_engine_defaults.emotion_server}
GLOBAL_RETRIES=3
SCHEDULE_PARAM=default
"""
