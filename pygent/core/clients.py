import logging

from openai import AsyncOpenAI
from supabase import Client, create_client

from . import config

# Supabase
if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
    logging.error(
        "SUPABASE_URL and SUPABASE_KEY must be set in the environment variables."
    )
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in the environment variables."
    )
supabase_client: Client = create_client(
    config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY
)

# OpenAI
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
