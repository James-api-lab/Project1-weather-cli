from pathlib import Path
from dotenv import load_dotenv
import os, requests, csv, datetime

# Load .env that lives in THIS folder (week2/.env)
load_dotenv(Path(__file__).with_name(".env"))
KEY = os.getenv("OPENWEATHER_API_KEY") or exit("Missing OPENWEATHER_API_KEY in week2/.env")

CITIES = ["Seattle", "London", "Tokyo"]         # change as you like
UNITS  = os.getenv("UNITS", "imperial")         # metric / imperial / standard
UNIT_LABEL = {"metric": "°C", "imperial": "°F", "standard": "K"}.get(UNITS, "")

# repo_root/data/weather_log.csv (works no matter where you run from)
repo_root = Path(__file__).parents[1]
log_path = repo_root / "data" / "weather_log.csv"
log_path.parent.mkdir(parents=True, exist_ok=True)

def fetch(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={KEY}&units={UNITS}"
    try:
        r = requests.get(url, timeout=20)
    except requests.exceptions.RequestException as e:
        return None, f"{city}: network error: {e}"
    if r.status_code != 200:
        return None, f"{city}: error {r.status_code}"
    try:
        d = r.json()
        return {
            "date": datetime.date.today().isoformat(),
            "city": d.get("name", city),
            "temp": d["main"]["temp"],          # unified temp column
            "units": UNITS,                     # write units per row
            "humidity": d["main"]["humidity"],
            "feels_like": d["main"]["feels_like"],
            "conditions": (d["weather"][0]["description"] if d.get("weather") else None),
        }, None
    except Exception as e:
        return None, f"{city}: bad JSON: {e}"

# simple de-dupe: don't append if (date, city) already exists
existing = set()
if log_path.exists():
    with log_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add((row.get("date"), row.get("city")))

wrote_header = log_path.exists()
with log_path.open("a", newline="", encoding="utf-8") as f:
    fieldnames = ["date", "city", "temp", "units", "humidity", "feels_like", "conditions"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not wrote_header:
        writer.writeheader()

    for c in CITIES:
        row, err = fetch(c)
        if err:
            print(err)
            continue
        key = (row["date"], row["city"])
        if key in existing:
            print(f"Skip {row['city']} (already logged for {row['date']})")
            continue
        writer.writerow(row)
        existing.add(key)  # catch duplicates within the same run
        print(f"Logged {row['city']}: {row['temp']:.2f}{UNIT_LABEL}, {row['conditions']}")
