import sys
import time
import json
import os
from scraper import scrape_url, ScrapingError
from summarizer import summarize_text, SummarizationError

DEFAULT_URL = "https://www.redfin.com"


def run_test(url: str) -> None:
    mode = "competitor"

    print(f"Scraping and summarizing URL: {url}")
    print(f"Mode: {mode}")
    print("-" * 50)

    start_time = time.time()

    try:
        # 1. Scrape
        print("Scraping started...")
        scraped_text = scrape_url(url)
        word_count = len(scraped_text.split())
        print(f"Scraped {word_count} words successfully.")

        # 2. Summarize
        print("Summarizing started...")
        summary_result = summarize_text(scraped_text, mode)

        processing_time = f"{time.time() - start_time:.2f}s"

        output = {
            "url": url,
            "mode": mode,
            "summary": summary_result["summary"],
            "key_points": summary_result["key_points"],
            "word_count": word_count,
            "processing_time": processing_time,
        }

        print("\nTest Result (JSON):")
        print(json.dumps(output, indent=2))

    except ScrapingError as e:
        print(f"Scraping failed: {e}")
        return
    except SummarizationError as e:
        print(f"Summarization failed: {e}")
        return
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return

    # Human-readable footer: warn the user if mock fallback may have been used
    allow_mock = os.environ.get("ALLOW_MOCK_SUMMARY", "true").lower() in ("true", "1", "yes")
    if allow_mock:
        print(
            "\n⚠️  Note: ALLOW_MOCK_SUMMARY is true — if Gemini fails, this fell back to mock data."
        )
    else:
        print(
            "\n✅  Note: ALLOW_MOCK_SUMMARY is false — this result came directly from the Gemini API."
        )


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    run_test(target_url)
