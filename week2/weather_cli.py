from pathlib import Path
from dotenv import load_dotenv
import os, requests, sys

# Load .env that lives in THIS folder (week2/.env)
load_dotenv(Path(__file__).with_name(".env"))

KEY = os.getenv("OPENWEATHER_API_KEY")
if not KEY:
    raise SystemExit("Missing OPENWEATHER_API_KEY in week2/.env")

def get_weather(city: str) -> str:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={KEY}&units=metric"
    r = requests.get(url, timeout=20)
    if r.status_code == 200:
        d = r.json()
        return f"{city}: {d['main']['temp']}°C, Humidity {d['main']['humidity']}%"
    if r.status_code == 404:
        return f"{city}: not found (check spelling)"
    if r.status_code == 401:
        return "Auth error: check OPENWEATHER_API_KEY in week2/.env"
    return f"Error {r.status_code}: {r.text[:140]}"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(get_weather(input("Enter a city: ").strip()))
    else:
        for c in sys.argv[1:]:
            print(get_weather(c))
