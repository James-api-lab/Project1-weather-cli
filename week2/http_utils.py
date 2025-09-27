# week2/http_utils.py
"""
HTTP utilities: a configured requests.Session with retries & backoff.
Why: connection pooling + resilience against temporary failures.
"""
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

def make_session() -> requests.Session:
    retry = Retry(
        total=3,                # up to 3 attempts
        connect=3,
        read=3,
        backoff_factor=0.5,     # 0.5s, 1s, 2s between retries
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,  # don't raise; we'll check status_code ourselves
    )
    adapter = HTTPAdapter(max_retries=retry)

    s = requests.Session()
    s.headers.update({"User-Agent": "weather-cli/0.1"})  # polite + debug
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s
