import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TAGS_TO_REMOVE = ["nav", "footer", "header", "script", "style", "aside"]
MAX_WORDS = 3000


def scrape_url(url):
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                return None

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        for tag in soup.find_all(TAGS_TO_REMOVE):
            tag.decompose()

        words = soup.get_text(separator=" ", strip=True).split()
        content = " ".join(words[:MAX_WORDS])

        return {"title": title, "content": content, "url": url}

    except Exception:
        return None
