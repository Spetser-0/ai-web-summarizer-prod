import time
from typing import List, Dict, Literal
from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, HttpUrl, Field
import uvicorn
from scraper import scrape_url, ScrapingError
from summarizer import summarize_text, SummarizationError

app = FastAPI(
    title="Web Scraper with AI Summarization API",
    description="A production-ready service to scrape content from a URL and summarize it using Google Gemini.",
    version="1.0.0"
)

# In-memory rate limiting storage: { ip: [timestamp1, timestamp2, ...] }
RATE_LIMIT_WINDOW = 60.0  # 1 minute in seconds
RATE_LIMIT_MAX_REQUESTS = 10
ip_request_history: Dict[str, List[float]] = {}


def check_rate_limit(client_ip: str) -> int:
    """
    Checks the request rate for a client IP.
    
    Args:
        client_ip (str): The IP address of the client.
        
    Returns:
        int: Seconds to wait if rate limit is exceeded, 0 otherwise.
    """
    now = time.time()
    
    # Initialize list if IP is new
    if client_ip not in ip_request_history:
        ip_request_history[client_ip] = []
        
    # Clean up timestamps older than the rate limit window
    ip_request_history[client_ip] = [
        t for t in ip_request_history[client_ip] 
        if now - t < RATE_LIMIT_WINDOW
    ]
    
    history = ip_request_history[client_ip]
    
    if len(history) >= RATE_LIMIT_MAX_REQUESTS:
        # Calculate how long before the oldest request falls out of the window
        oldest_request = history[0]
        wait_time = int(oldest_request + RATE_LIMIT_WINDOW - now)
        return max(1, wait_time)
        
    # Log current request timestamp
    history.append(now)
    return 0


# Pydantic schemas
class SummarizeRequest(BaseModel):
    url: HttpUrl = Field(
        ..., 
        description="The HTTP/HTTPS URL of the webpage to scrape and summarize.",
        examples=["https://news.ycombinator.com"]
    )
    mode: Literal["quick", "detailed", "competitor"] = Field(
        default="quick",
        description="The summarization mode: 'quick' (3 bullets), 'detailed' (deep insights), or 'competitor' (strategic analysis)."
    )


class SummarizeResponse(BaseModel):
    url: str = Field(..., description="The analyzed URL.")
    mode: str = Field(..., description="Summarization mode used.")
    summary: str = Field(..., description="The AI-generated summary text.")
    key_points: List[str] = Field(..., description="List of key points or bulleted takeaways.")
    word_count: int = Field(..., description="Word count of the scraped content.")
    processing_time: str = Field(..., description="Time taken to process request (e.g. '2.45s').")


@app.post(
    "/summarize",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape and summarize a URL",
    responses={
        429: {
            "description": "Too Many Requests. Rate limit exceeded.",
            "headers": {
                "Retry-After": {
                    "schema": {"type": "integer"},
                    "description": "The number of seconds to wait before making another request."
                }
            }
        },
        400: {"description": "Invalid input URL or bad request."},
        502: {"description": "Scraping failed or was blocked by the target site."},
        503: {"description": "AI summarization service unavailable."}
    }
)
async def summarize(payload: SummarizeRequest, request: Request, response: Response):
    # Retrieve client IP
    client_ip = request.client.host if request.client else "unknown-ip"
    
    # Enforce rate limit
    wait_time = check_rate_limit(client_ip)
    if wait_time > 0:
        response.headers["Retry-After"] = str(wait_time)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
        )

    start_time = time.time()
    url_str = str(payload.url)

    # 1. Scrape content
    try:
        scraped_text = scrape_url(url_str)
    except ScrapingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Scraping failed: {str(e)}"
        )

    # Calculate word count of scraped text
    word_count = len(scraped_text.split())

    # 2. Summarize content
    try:
        summary_result = summarize_text(scraped_text, payload.mode)
    except SummarizationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI Summarization failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during summarization: {str(e)}"
        )

    processing_time = f"{time.time() - start_time:.2f}s"

    return SummarizeResponse(
        url=url_str,
        mode=payload.mode,
        summary=summary_result["summary"],
        key_points=summary_result["key_points"],
        word_count=word_count,
        processing_time=processing_time
    )


@app.get("/health", status_code=status.HTTP_200_OK, summary="Health Check")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    # Load configuration from environment
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    
    print(f"Starting server on http://{host}:{port}")
    uvicorn.run("api:app", host=host, port=port, reload=True)
