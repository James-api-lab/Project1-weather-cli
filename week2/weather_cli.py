# week2/weather_cli.py
from pathlib import Path
from dotenv import load_dotenv
import os, argparse, logging
from logging.handlers import RotatingFileHandler
import requests
from http_utils import make_session

# --- config & env ---
load_dotenv(Path(__file__).with_name(".env"))
KEY = os.getenv("OPENWEATHER_API_KEY") or exit("Missing OPENWEATHER_API_KEY in week2/.env")
BASE = "https://api.openweathermap.org/data/2.5/weather"

TIMEOUT = 10



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

# --- helpers ---
def unit_label(units: str) -> str:
    return {"metric": "°C", "imperial": "°F", "standard": "K"}.get(units, "")

def parse_args():
    p = argparse.ArgumentParser(description="Weather CLI")
    p.add_argument("cities", nargs="*", help='City names (e.g., Seattle "New York")')
    p.add_argument("--units", choices=["metric","imperial","standard"],
                   default=os.getenv("UNITS","metric"),
                   help="Units: metric(°C), imperial(°F), standard(K).")
    p.add_argument("--timeout", type=int, default=int(os.getenv("TIMEOUT","10")),
                   help="Per-request timeout in seconds (default 10 or TIMEOUT env).")
    p.add_argument("--retries", type=int, default=int(os.getenv("RETRIES","3")),
                   help="Retry attempts for transient errors (default 3 or RETRIES env).")
    p.add_argument("--backoff", type=float, default=float(os.getenv("BACKOFF","0.5")),
                   help="Exponential backoff factor (default 0.5).")
    p.add_argument("--cities-file", type=str,
                   help="Path to a text file with one city per line (optional).")
    return p.parse_args()


def setup_logging():
    log_dir = Path(__file__).parents[1] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_dir / "weather-cli.log",
                                  maxBytes=200_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger("weather_cli")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

def fetch_and_format(city: str, units: str, session: requests.Session, timeout: int) -> str:
    url = f"{BASE}?q={city}&appid={KEY}&units={units}"
    try:
        r = session.get(url, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return f"Network error for {city}: {e}"

    if r.status_code == 200:
        try:
            d = r.json()
            temp = d["main"]["temp"]
            hum = d["main"]["humidity"]
        except Exception:
            return f"Error: unexpected JSON {r.text[:140]}"
        return f"{city}: {temp:.2f}{unit_label(units)}, Humidity {hum}%"

    if r.status_code == 404:
        return f"{city}: not found (check spelling)"
    if r.status_code == 401:
        return "Auth error: check OPENWEATHER_API_KEY in week2/.env"
    if r.status_code in (429, 500, 502, 503, 504):
        return f"Temporary server issue ({r.status_code}). Please try again."
    return f"Error {r.status_code}: {r.text[:140]}"

# --- main ---
if __name__ == "__main__":
    args = parse_args()
    logger = setup_logging()
    logger.info("run units=%s timeout=%s retries=%s backoff=%s cities=%s",
                args.units, args.timeout, args.retries, args.backoff, args.cities)

    session = make_session(total=args.retries, backoff=args.backoff)
    timeout = args.timeout

    # merge cities from file + positional
    cities = list(args.cities)
    if args.cities_file:
        with open(Path(args.cities_file), "r", encoding="utf-8") as f:
            cities.extend([line.strip() for line in f if line.strip()])

    if not cities:
        cities = [input("Enter a city: ").strip()]

    for c in cities:
        result = fetch_and_format(c, args.units, session, timeout)
        print(result)
        logger.info(result)
