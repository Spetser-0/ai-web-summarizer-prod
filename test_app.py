import time
import json
from scraper import scrape_url, ScrapingError
from summarizer import summarize_text, SummarizationError

def run_test():
    url = "https://news.ycombinator.com"
    mode = "quick"
    
    print(f"Scraping and summarizing URL: {url}")
    print(f"Mode: {mode}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # 1. Scrape
        scraped_text = scrape_url(url)
        word_count = len(scraped_text.split())
        print(f"Scraped {word_count} words successfully.")
        
        # 2. Summarize
        summary_result = summarize_text(scraped_text, mode)
        
        processing_time = f"{time.time() - start_time:.2f}s"
        
        output = {
            "url": url,
            "mode": mode,
            "summary": summary_result["summary"],
            "key_points": summary_result["key_points"],
            "word_count": word_count,
            "processing_time": processing_time
        }
        
        print("\nTest Result (JSON):")
        print(json.dumps(output, indent=2))
        
    except ScrapingError as e:
        print(f"Scraping failed: {e}")
    except SummarizationError as e:
        print(f"Summarization failed: {e}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    run_test()
