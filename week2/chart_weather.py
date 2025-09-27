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

# read CSV → group by city
series = {}  # city -> {"dates": [], "temps": []}
with csv_path.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        city = row["city"]
        dt = datetime.fromisoformat(row["date"])  # supports date or datetime ISO
        temp = float(row["temp_c"])
        s = series.setdefault(city, {"dates": [], "temps": []})
        s["dates"].append(dt)
        s["temps"].append(temp)

# plot (show single points + tighten x-axis)
plt.figure(figsize=(9, 5))
all_dates = []

for city, data in sorted(series.items()):
    pairs = sorted(zip(data["dates"], data["temps"]), key=lambda x: x[0])
    if not pairs:
        continue
    dates, temps = zip(*pairs)
    all_dates.extend(dates)

    if len(dates) == 1:
        plt.scatter(dates, temps, label=city)
    else:
        plt.plot(dates, temps, marker="o", linewidth=2, label=city)

if all_dates:
    xmin, xmax = min(all_dates), max(all_dates)
    pad = timedelta(days=1)
    plt.xlim(xmin - pad, xmax + pad)

ax = plt.gca()
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
plt.gcf().autofmt_xdate()
plt.title("Daily Temperature by City")
plt.xlabel("Date")
plt.ylabel("Temp (°C)")
plt.grid(True, alpha=0.3)
plt.legend(loc="best")
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(out_path, dpi=150)
print(f"Saved chart → {out_path}")
