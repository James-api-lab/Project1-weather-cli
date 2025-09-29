# week2/run_log_and_chart.py
from pathlib import Path
from dotenv import load_dotenv
import subprocess, sys, os

def main():
    repo_root = Path(__file__).parents[1]
    env_file = repo_root / "week2" / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    py = sys.executable
    log_script = repo_root / "week2" / "log_weather_daily.py"
    chart_script = repo_root / "week2" / "chart_weather.py"

    subprocess.run([py, str(log_script)], check=True, cwd=repo_root)
    subprocess.run([py, str(chart_script)], check=True, cwd=repo_root)

    out_png = repo_root / "data" / "weather_chart.png"
    print(f"✓ Logged and chart generated → {out_png}")
    if os.name == "nt" and os.getenv("OPEN_CHART") == "1" and out_png.exists():
        os.startfile(str(out_png))
