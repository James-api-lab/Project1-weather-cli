# week2/weather_cli.py
from pathlib import Path
from dotenv import load_dotenv
import os, argparse, logging
from logging.handlers import RotatingFileHandler
import requests
from http_utils import make_session
import json, csv, datetime



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
    p.add_argument("--json", action="store_true",
               help="Output one JSON object per city instead of human text")
    # add/replace your csv-out arg
    p.add_argument("--csv-out", type=str, default=os.getenv("CSV_OUT"),
               help="Append this run to a CSV (default from CSV_OUT env if set)")
    return p.parse_args()

def fetch_raw(city: str, units: str, session: requests.Session, timeout: int) -> dict:
    """Return a normalized dict with either data or an error (no printing here)."""
    url = f"{BASE}?q={city}&appid={KEY}&units={units}"
    try:
        r = session.get(url, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {"ok": False, "city": city, "units": units, "error": f"network: {e}"}

    if r.status_code == 200:
        try:
            d = r.json()
            return {
                "ok": True,
                "city": d.get("name", city),
                "units": units,
                "temp": d["main"]["temp"],
                "feels_like": d["main"]["feels_like"],
                "humidity": d["main"]["humidity"],
                "conditions": (d["weather"][0]["description"] if d.get("weather") else None),
            }
        except Exception:
            return {"ok": False, "city": city, "units": units, "error": "bad json"}
    if r.status_code == 404:
        return {"ok": False, "city": city, "units": units, "error": "not found"}
    if r.status_code == 401:
        return {"ok": False, "city": city, "units": units, "error": "auth"}
    if r.status_code in (429, 500, 502, 503, 504):
        return {"ok": False, "city": city, "units": units, "error": f"server {r.status_code}"}
    return {"ok": False, "city": city, "units": units, "error": f"status {r.status_code}"}


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
    # parse + logging
    args = parse_args()
    logger = setup_logging()
    logger.info("run units=%s timeout=%s retries=%s backoff=%s cities=%s",
                args.units, args.timeout, args.retries, args.backoff, args.cities)

    # session + timeout from args
    session = make_session(total=args.retries, backoff=args.backoff)
    timeout = args.timeout

    # merge cities from file + positional
    cities = list(args.cities)
    if args.cities_file:
        with open(Path(args.cities_file), "r", encoding="utf-8") as f:
            cities.extend([line.strip() for line in f if line.strip()])
    if not cities:
        cities = [input("Enter a city: ").strip()]

    # optional CSV writer (default can come from CSV_OUT env via parse_args)
    writer = None
    existing = set()  # (date, city)
    today = datetime.date.today().isoformat()
    if args.csv_out:
        out_path = Path(args.csv_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        need_header = not out_path.exists()

        # build "already logged today" set to avoid duplicates
        if out_path.exists():
            with out_path.open("r", encoding="utf-8", newline="") as rf:
                for row in csv.DictReader(rf):
                    d, c = row.get("date"), row.get("city")
                    if d and c:
                        existing.add((d, c))

        f = out_path.open("a", newline="", encoding="utf-8")
        writer = csv.DictWriter(f, fieldnames=[
            "date","city","temp","units","humidity","feels_like","conditions"
        ])
        if need_header:
            writer.writeheader()

        def write_unique_row(payload: dict):
            """Write only if (today, city) hasn't been logged yet."""
            key = (today, payload["city"])
            if key in existing:
                logger.info("skip duplicate row %s %s", *key)
                return
            writer.writerow({
                "date": today,
                "city": payload["city"],
                "temp": payload["temp"],
                "units": payload["units"],
                "humidity": payload["humidity"],
                "feels_like": payload["feels_like"],
                "conditions": payload["conditions"],
            })
            existing.add(key)

    # main loop
    for c in cities:
        if args.json:
            payload = fetch_raw(c, args.units, session, timeout)
            print(json.dumps({"date": today, **payload}, ensure_ascii=False))
            logger.info(payload if payload.get("ok") else f"ERR {payload}")
            if writer and payload.get("ok"):
                write_unique_row(payload)
        else:
            result = fetch_and_format(c, args.units, session, timeout)
            print(result)
            logger.info(result)
            if writer and "Error" not in result and "not found" not in result and "Auth error" not in result:
                payload = fetch_raw(c, args.units, session, timeout)
                if payload.get("ok"):
                    write_unique_row(payload)

    if writer:
        f.close()
