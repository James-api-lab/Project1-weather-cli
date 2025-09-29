Here’s a copy-paste README that will make your repo clear and runnable.

````markdown
# Project1-weather-cli

A tiny, production-ish **Weather CLI** in Python.  
Fetch live temps for one or many cities, log daily readings to CSV, and generate a chart.

---

## Features
- **CLI flags** via `argparse` (`--units`, `--timeout`, `--retries`, `--backoff`, `--cities-file`)
- **Reliable HTTP** with a `requests.Session` + retries/backoff + timeouts
- **Daily logger** → `data/weather_log.csv` (unit-aware)
- **Chart generator** → `data/weather_chart.png`
- **Rotating run log** → `logs/weather-cli.log`

---

## Quickstart

### Prereqs
- Python **3.11+**
- An OpenWeather API key

### Setup
```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # (Windows)  Mac/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install requests python-dotenv matplotlib
````

### Environment

Create `week2/.env` (do NOT commit real keys):

```
OPENWEATHER_API_KEY=your_key_here
UNITS=metric    # or imperial (optional default for CLI)
```

---

## Run

### One-off scripts

```powershell
python week2/weather_one_city.py
```

### CLI usage

```powershell
# cities as positional args
python week2/weather_cli.py --units imperial "New York" London

# different units
python week2/weather_cli.py --units metric Seattle Tokyo

# prompt mode (no args)
python week2/weather_cli.py

# tune reliability
python week2/weather_cli.py --timeout 5 --retries 5 --backoff 1.0 London

# read cities from a file (one per line)
python week2/weather_cli.py --units imperial --cities-file cities.txt

### JSON & one-off CSV
```bash
# JSON lines (one per city)
python week2/weather_cli.py --units imperial "New York" London --json

# Append to the main log (via .env CSV_OUT)
python week2/weather_cli.py --units metric Seattle Tokyo
```

**Flags**

* `--units {metric,imperial,standard}` → prints °C/°F/K accordingly
* `--timeout INT` (seconds)
* `--retries INT` (transient 429/5xx)
* `--backoff FLOAT` (exponential backoff)
* `--cities-file PATH` (one city per line)

---

## Daily logging

Append today’s readings for selected cities to a CSV:

```powershell
python week2/log_weather_daily.py
```

Creates/updates: `data/weather_log.csv` with columns:

```
date,city,temp,units,humidity,feels_like,conditions
```

(Optional Windows scheduling: Task Scheduler → point to `.venv\Scripts\python.exe` and `week2\log_weather_daily.py`.)

---

## Chart

Turn your CSV into a line chart:

```powershell
python week2/chart_weather.py
```

Outputs: `data/weather_chart.png`
(Shows dots when there’s only one data point; auto-labels °C/°F from CSV.)

---

## Logs

CLI runs are written to `logs/weather-cli.log` (rotates automatically).

```powershell
Get-Content .\logs\weather-cli.log -Tail 20
```

---

## Project structure

```
Project1-weather-cli/
  data/
    weather_log.csv
    weather_chart.png
  logs/
    weather-cli.log
  week2/
    .env                 # your real key (gitignored)
    weather_one_city.py
    weather_cli.py
    log_weather_daily.py
    chart_weather.py
    http_utils.py
```

---

## Troubleshooting

* **Missing OPENWEATHER_API_KEY**
  Ensure `week2/.env` has `OPENWEATHER_API_KEY=...` and you’re running the scripts from repo root or `week2/`.

* **401 Unauthorized**
  Bad/expired key. Update the value in `week2/.env`.

* **404 city not found**
  Check spelling, use quotes for spaces: `"New York"`.

* **ModuleNotFoundError: dotenv / matplotlib**
  `pip install python-dotenv matplotlib`

* **Chart shows “Temp (°C)” but you log °F**
  Ensure the CSV header is the unit-aware schema (`temp,units,...`). If you have an old `temp_c` file, run the logger once to regenerate or migrate.

---

## Why sessions & retries?

`http_utils.make_session()` reuses connections and automatically retries transient errors with backoff so your daily jobs are faster and more reliable.






