# week2/http_utils.py
"""
HTTP utilities: a configured requests.Session with retries & backoff.
Why: connection pooling + resilience against temporary failures.
"""
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

def make_session(
    total: int = 3,
    backoff: float = 0.5,
    status_forcelist = (429, 500, 502, 503, 504),
    allowed_methods = ("GET", "POST"),
    user_agent: str = "weather-cli/0.1",
) -> requests.Session:
    retry = Retry(
        total=total,
        connect=total,
        read=total,
        backoff_factor=backoff,          # 0.5s, 1.0s, 2.0s ...
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False,
        respect_retry_after_header=True, # honor server Retry-After
    )

    adapter = HTTPAdapter(max_retries=retry)

    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s
