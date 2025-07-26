"""Default initialization content."""

from .defaults import anna_engine_defaults

INIT_YAML = f"""\
model_service:
  model_name: {anna_engine_defaults.model_name}
  api_key: {anna_engine_defaults.api_key}
  base_url: {anna_engine_defaults.base_url}
servers:
  complaint:
    api_key: {anna_engine_defaults.complaint_api_key}
    base_url: {anna_engine_defaults.complaint_base_url}
  counselor:
    api_key: {anna_engine_defaults.counselor_api_key}
    base_url: {anna_engine_defaults.counselor_base_url}
  emotion:
    api_key: {anna_engine_defaults.emotion_api_key}
    base_url: {anna_engine_defaults.emotion_base_url}
"""

INIT_DOTENV = """\
GLOBAL_RETRIES=3
SCHEDULE_PARAM=default
"""
