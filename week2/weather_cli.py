# week2/weather_cli.py
from pathlib import Path
from dotenv import load_dotenv
import os, argparse, logging, json, csv, datetime
from logging.handlers import RotatingFileHandler
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed



# IMPORTANT: support both package usage ("weather" command) and direct script run
try:
    from .http_utils import make_session  # when installed as a package
except ImportError:
    from http_utils import make_session   # when running: python week2/weather_cli.py

VERSION = "0.1.0"


# --- config & env ---
load_dotenv(Path(__file__).with_name(".env"))
KEY = os.getenv("OPENWEATHER_API_KEY") or exit("Missing OPENWEATHER_API_KEY in week2/.env")
BASE = "https://api.openweathermap.org/data/2.5/weather"

TIMEOUT = 10

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
    p.add_argument("--version", action="version", version="weather-cli 0.1.0")
    p.add_argument("--max-workers", type=int, default=int(os.getenv("MAX_WORKERS", "0")),
               help="Max parallel requests (0=auto).")
    p.add_argument("--cache-day", action="store_true",
               help="Cache successful responses for the current day (per units) and reuse them.")
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

def fetch_parallel(cities, units, retries, backoff, timeout, use_cache=False):
    """
    Return list of (input_city, payload) preserving input order.
    Caches by lowercased input city for today's date+units.
    """
    results = [None] * len(cities)

    # load cache (if any)
    cache = {}
    cpath = None
    if use_cache:
        cpath = _cache_path(units)
        if cpath.exists():
            try:
                cache = json.loads(cpath.read_text(encoding="utf-8"))
            except Exception:
                cache = {}

    # worker
    def work(idx_city):
        idx, city = idx_city
        key = city.strip().lower()
        if use_cache and key in cache:
            return (idx, city, cache[key])

        session = _new_session(retries, backoff)  # 1 session per task (requests.Session isn’t thread-safe)
        payload = fetch_raw(city, units, session, timeout)
        if use_cache and payload.get("ok"):
            cache[key] = payload
        return (idx, city, payload)

    # run
    max_workers = min(max(1, len(cities)), 8)  # default cap; you can tune
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for idx, city, payload in ex.map(work, enumerate(cities)):
            results[idx] = (city, payload)

    # write cache back if changed
    if use_cache and cpath:
        try:
            cpath.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    return results

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

def _new_session(retries: int, backoff: float) -> requests.Session:
    """Create a session; supports both param and no-param make_session()."""
    try:
        return make_session(total=retries, backoff=backoff)  # your newer util
    except TypeError:
        return make_session()  # fallback if util has no args

def _cache_path(units: str) -> Path:
    """data/cache/YYYY-MM-DD_units.json"""
    root = Path(__file__).parents[1]
    cdir = root / "data" / "cache"
    cdir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    return cdir / f"{today}_{units}.json"


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


def main():
    args = parse_args()
    logger = setup_logging()
    logger.info("run units=%s timeout=%s retries=%s backoff=%s cities=%s",
                args.units, args.timeout, args.retries, args.backoff, args.cities)

    # base session/timeout (used for sequential path)
    session = make_session(total=args.retries, backoff=args.backoff)
    timeout = args.timeout

    # merge cities from file + positional
    cities = list(args.cities)
    if args.cities_file:
        with open(Path(args.cities_file), "r", encoding="utf-8") as f:
            cities.extend([line.strip() for line in f if line.strip()])
    if not cities:
        cities = [input("Enter a city: ").strip()]

    # optional CSV writer (respects CSV_OUT)
    writer = None
    existing = set()
    today = datetime.date.today().isoformat()
    if args.csv_out:
        out_path = Path(args.csv_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        need_header = not out_path.exists()

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

    # ---------- parallel/caching decision (once) ----------
    max_workers = args.max_workers or min(max(1, len(cities)), 8)
    use_cache = bool(args.cache_day)

    # fetch all cities (parallel or sequential)
    if max_workers > 1:
        results = fetch_parallel(cities, args.units, args.retries, args.backoff, timeout, use_cache)
    else:
        results = []
        for city in cities:
            payload = fetch_raw(city, args.units, session, timeout)
            results.append((city, payload))

    # print/log/write in input order
    for city_input, payload in results:
        if args.json:
            print(json.dumps({"date": today, **payload}, ensure_ascii=False))
            logger.info(payload if payload.get("ok") else f"ERR {payload}")
        else:
            if payload.get("ok"):
                msg = f"{payload['city']}: {payload['temp']:.2f}{unit_label(args.units)}, Humidity {payload['humidity']}%"
            else:
                err = payload.get("error", "unknown")
                city = payload.get("city", city_input)
                if err == "not found":
                    msg = f"{city}: not found (check spelling)"
                elif err == "auth":
                    msg = "Auth error: check OPENWEATHER_API_KEY in week2/.env"
                elif err.startswith("server"):
                    code = err.split()[-1]
                    msg = f"Temporary server issue ({code}). Please try again."
                elif err.startswith("network"):
                    msg = f"Network error for {city}: {err.split(':',1)[-1].strip()}"
                else:
                    msg = f"Error: {err}"
            print(msg)
            logger.info(msg)

        # CSV write (once)
        if writer and payload.get("ok"):
            write_unique_row(payload)

    if writer:
        f.close()

if __name__ == "__main__":
    main()
