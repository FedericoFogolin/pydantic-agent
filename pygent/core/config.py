import os
from dotenv import load_dotenv

load_dotenv()

# LLM Models
REASONER_LLM_MODEL = os.getenv("REASONER_MODEL", "o3-mini")
PRIMARY_LLM_MODEL = os.getenv("PRIMARY_MODEL", "gpt-4o")
SMALL_LLM_MODEL = os.getenv("SMALL_MODEL", "gpt-4.1-mini")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Embedding Model
EMBEDDING_MODEL = "text-embedding-3-small"
