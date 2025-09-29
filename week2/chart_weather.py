from pathlib import Path
import csv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# paths
repo_root = Path(__file__).parents[1]
csv_path = repo_root / "data" / "weather_log.csv"
out_path = repo_root / "data" / "weather_chart.png"

if not csv_path.exists():
    raise SystemExit(f"Missing {csv_path}. Run log_weather_daily.py first.")

# unit labels + the set of units we see in the CSV
unit_label = {"metric": "°C", "imperial": "°F", "standard": "K"}
units_seen = set()

# read CSV → group by city
# supports both old logs (temp_c) and new logs (temp + units)
series = {}  # city -> {"dates": [], "temps": []}
with csv_path.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        city = row.get("city")
        if not city:
            continue
        # date can be ISO date or datetime
        try:
            dt = datetime.fromisoformat(row["date"])
        except Exception:
            continue

        # temp field fallback: prefer "temp" else use "temp_c"
        temp_str = row.get("temp") or row.get("temp_c")
        if temp_str is None:
            continue
        try:
            temp = float(temp_str)
        except ValueError:
            continue

        # units: from column if present; otherwise infer from legacy column name
        u = row.get("units")
        if not u:
            u = "metric" if "temp_c" in row else "metric"  # safe default
        units_seen.add(u)

        s = series.setdefault(city, {"dates": [], "temps": []})
        s["dates"].append(dt)
        s["temps"].append(temp)

# plot (show single points + tighten axes)
plt.figure(figsize=(9, 5))
all_dates, all_temps = [], []

for city, data in sorted(series.items()):
    pairs = sorted(zip(data["dates"], data["temps"]), key=lambda x: x[0])
    if not pairs:
        continue
    dates, temps = zip(*pairs)
    all_dates.extend(dates)
    all_temps.extend(temps)

    if len(dates) == 1:
        plt.scatter(dates, temps, label=city)
    else:
        plt.plot(dates, temps, marker="o", linewidth=2, label=city)

# tighten x/y ranges
if all_dates:
    xmin, xmax = min(all_dates), max(all_dates)
    pad = timedelta(days=1)
    plt.xlim(xmin - pad, xmax + pad)
if all_temps:
    ypad = 2
    plt.ylim(min(all_temps) - ypad, max(all_temps) + ypad)

# date formatting
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
plt.gcf().autofmt_xdate()

# y-axis label from units seen
ylabel = "Temp"
if len(units_seen) == 1:
    u = next(iter(units_seen))
    ylabel = f"Temp ({unit_label.get(u, u)})"
plt.ylabel(ylabel)

plt.title("Daily Temperature by City")
plt.xlabel("Date")
plt.grid(True, alpha=0.3)
plt.legend(loc="best")
plt.tight_layout()
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_path, dpi=150)
print(f"Saved chart → {out_path}")
