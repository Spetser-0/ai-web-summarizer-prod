import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

class ScrapingError(Exception):
    """Custom exception raised when scraping fails or is blocked."""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


def scrape_url(url: str) -> str:
    """
    Fetches the content of the given URL and extracts clean, readable text.
    
    Args:
        url (str): The target webpage URL to scrape.
        
    Returns:
        str: Cleaned, readable text extracted from the webpage.
        
    Raises:
        ScrapingError: If the request fails, returns a non-200 status code,
                       or is blocked by the website.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.Timeout:
        raise ScrapingError("Request to the URL timed out after 15 seconds.", 408)
    except requests.exceptions.ConnectionError:
        raise ScrapingError("Failed to connect to the server. Please check the URL or your internet connection.", 503)
    except requests.exceptions.RequestException as e:
        raise ScrapingError(f"An unexpected connection error occurred: {str(e)}", 500)

    # Check for blocking or failure status codes
    if response.status_code == 403:
        raise ScrapingError(
            "Access forbidden. The website is blocking our scraper (403 Forbidden).", 
            403
        )
    elif response.status_code == 429:
        raise ScrapingError(
            "Too many requests. The website is rate-limiting requests (429 Too Many Requests).", 
            429
        )
    elif response.status_code != 200:
        raise ScrapingError(
            f"Failed to retrieve the webpage. Server returned status code {response.status_code}.", 
            response.status_code
        )

    # Parse content
    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        raise ScrapingError(f"Failed to parse HTML content: {str(e)}", 500)

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript", "svg"]):
        tag.decompose()

    # Extract text content from main elements
    text_blocks = []
    # Focus on main textual elements
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "article"]):
        text = element.get_text().strip()
        if text:
            # Avoid duplicating text from nested structures if already collected
            if not any(text in block for block in text_blocks):
                text_blocks.append(text)

    # Fallback to general text if no semantic tags found
    if not text_blocks:
        body_text = soup.get_text()
        text_blocks = [line.strip() for line in body_text.splitlines() if line.strip()]

    cleaned_text = "\n\n".join(text_blocks)

    if not cleaned_text.strip():
        raise ScrapingError(
            "The webpage contains no readable text or the content is entirely dynamic (requires JavaScript).",
            204
        )

    return cleaned_text
