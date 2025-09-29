$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$root\.venv\Scripts\python.exe" "$root\week2\log_weather_daily.py"
