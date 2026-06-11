import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UAZAPI_TOKEN = os.getenv("UAZAPI_TOKEN")
UAZAPI_URL = os.getenv("UAZAPI_URL")
