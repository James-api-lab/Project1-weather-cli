# week2/weather_one_city.py
from pathlib import Path
from dotenv import load_dotenv
import os, requests

# Load the .env that lives in the SAME folder as this file
load_dotenv(Path(__file__).with_name(".env"))

KEY = os.getenv("OPENWEATHER_API_KEY") or exit("Missing OPENWEATHER_API_KEY in week2/.env")

city = "Sao Paulo"
url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={KEY}&units=imperial"
r = requests.get(url, timeout=20)
d = r.json()
print(f"{city}: {d['main']['temp']}°C, Humidity {d['main']['humidity']}%")
