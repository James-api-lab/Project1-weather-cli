# week2/weather_cli.py
from pathlib import Path
from dotenv import load_dotenv
import os, requests, sys

# add temporarily at the top of weather_cli.py
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)


from http_utils import make_session   # <-- NEW

# Load .env that lives in THIS folder (week2/.env)
load_dotenv(Path(__file__).with_name(".env"))

KEY = os.getenv("OPENWEATHER_API_KEY")
if not KEY:
    raise SystemExit("Missing OPENWEATHER_API_KEY in week2/.env")

BASE = "https://api.openweathermap.org/data/2.5/weather"
UNITS = "imperial"
TIMEOUT = 10  # seconds
SESSION = make_session()  # <-- NEW (reuse across calls)

def get_weather(city: str) -> str:
    """Fetch weather for one city with retries, timeouts, and friendly errors."""
    url = f"{BASE}?q={city}&appid={KEY}&units={UNITS}"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)  # <-- NEW: use the session
    except requests.exceptions.RequestException as e:
        return f"Network error for {city}: {e}"

    if r.status_code == 200:
        try:
            d = r.json()
        except ValueError:
            return f"Error: non-JSON response ({len(r.text)} bytes)"
        try:
            return f"{city}: {d['main']['temp']}°, Humidity {d['main']['humidity']}%"
        except KeyError:
            return f"Error: JSON missing expected keys: {d}"

    if r.status_code == 404:
        return f"{city}: not found (check spelling)"
    if r.status_code == 401:
        return "Auth error: check OPENWEATHER_API_KEY in week2/.env"
    if r.status_code in (429, 500, 502, 503, 504):
        return f"Temporary server issue ({r.status_code}). Please try again."

    return f"Error {r.status_code}: {r.text[:140]}"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(get_weather(input("Enter a city: ").strip()))
    else:
        for c in sys.argv[1:]:
            print(get_weather(c))
