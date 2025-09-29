Project1-weather-cli

A tiny, production-ish Weather CLI in Python.
Fetch live temps for one or many cities, log daily readings to CSV, and generate a chart.

Features

CLI flags via argparse (--units, --timeout, --retries, --backoff, --cities-file, --json, --csv-out, --version)

Reliable HTTP: requests.Session + retries/backoff + timeouts

Daily logger → data/weather_log.csv (de-dupes by (date, city))

Chart generator → data/weather_chart.png (unit-aware axis)

One-command runner → weather-daily (log → chart)

Faster runs: --max-workers parallel fetch + --cache-day same-day cache

Quickstart
Prereqs

Python 3.11+

OpenWeather API key

Setup (Windows PowerShell)
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# install project in editable mode (creates `weather` and `weather-daily` commands)
pip install -e .

Configure secrets

Create week2/.env:

OPENWEATHER_API_KEY=your_api_key_here
# optional defaults
UNITS=imperial
CSV_OUT=data/weather_log.csv


Tip: .gitignore already excludes week2/.env and generated files.

Usage
Basic
weather --version
weather --units imperial "New York" London
weather --units metric Seattle Tokyo --json

From a file
# cities.txt with one city per line
weather --cities-file week2\cities.txt --units imperial

Log → Chart (one command)
# runs the logger then redraws the chart
$env:OPEN_CHART = "1"    # optional: auto-open the PNG on Windows
weather-daily

Performance options
# parallel requests (auto-picks a sensible value if omitted)
weather --max-workers 6 "New York" London Tokyo Paris

# same-day cache (per-units) to avoid re-fetching
weather --cache-day Seattle Chicago Boston

# combine with logging (de-dupes rows by date/city)
weather --cache-day --csv-out data/weather_log.csv "San Francisco" Miami

Outputs

data/weather_log.csv — main data log (date, city, temp, units, humidity, feels_like, conditions)

data/weather_chart.png — chart of temps over time (per city)

data/cache/YYYY-MM-DD_units.json — same-day cache (optional, via --cache-day)

logs/weather-cli.log — rotating run log

Project structure
Project1-weather-cli/
  README.md
  pyproject.toml
  .gitignore
  week2/
    __init__.py
    http_utils.py
    weather_cli.py
    log_weather_daily.py
    chart_weather.py
    run_log_and_chart.py
    .env                 # not tracked
  data/                  # generated (ignored)
  logs/                  # generated (ignored)

Troubleshooting

weather-daily: not recognized → run pip install -e . --no-deps --force-reinstall, then reopen your shell and re-activate the venv.

ModuleNotFoundError: http_utils → ensure imports in weather_cli.py use:

try:
    from .http_utils import make_session
except ImportError:
    from http_utils import make_session


Temps look wrong (°C vs °F) → set UNITS in week2/.env, regenerate the chart.
