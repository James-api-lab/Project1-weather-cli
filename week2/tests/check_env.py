# week2/check_env.py
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(filename="week2/.env", usecwd=True) or "week2/.env")

names = ["OPENWEATHER_API_KEY", "NEWSAPI_API_KEY", "OPENAI_API_KEY", "SENDGRID_API_KEY"]
for n in names:
    print(f"{n}: {'SET' if os.getenv(n) else 'MISSING'}")
