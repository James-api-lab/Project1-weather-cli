# week2/settings.py
import os
from dotenv import load_dotenv, find_dotenv

# Find week2/.env no matter where you run from
env_path = find_dotenv(filename="week2/.env", usecwd=True)
load_dotenv(env_path or "week2/.env")

def require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise SystemExit(f"Missing {name}. Add it to week2/.env")
    return val

# Required for Week 2
OPENWEATHER_API_KEY = require("OPENWEATHER_API_KEY")

# Optional (you added them—great for later projects)
NEWSAPI_API_KEY   = os.getenv("NEWSAPI_API_KEY")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY  = os.getenv("SENDGRID_API_KEY")
