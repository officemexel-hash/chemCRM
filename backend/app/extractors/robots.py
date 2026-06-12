from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


def can_fetch(url: str, user_agent: str = "ChemicalSourcingRFQCRM/0.1") -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        response = httpx.get(robots_url, timeout=8)
        if response.status_code >= 400:
            return True
        parser.parse(response.text.splitlines())
        return parser.can_fetch(user_agent, url)
    except httpx.HTTPError:
        return True
