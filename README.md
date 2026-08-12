# 🔍 AI Web Summarizer

> Scrape any URL. Get structured AI insights in seconds.

A production-ready Python service that fetches any webpage, extracts clean text, and returns a structured AI-powered summary via a REST API — built with FastAPI and Google Gemini.

---

## ✨ Live Demo

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.zillow.com/homes/for_sale/", "mode": "competitor"}'
```

```json
{
  "url": "https://www.zillow.com/homes/for_sale/",
  "mode": "competitor",
  "summary": "Zillow operates as a real estate marketplace connecting buyers, sellers, and agents through property listings, valuation estimates (Zestimate), and lead-generation tools for agents. Revenue is driven primarily by agent advertising (Premier Agent) and mortgage/lending referrals rather than transaction fees.",
  "key_points": [
    "Monetizes through agent advertising placement rather than listing fees, creating a two-sided marketplace dynamic.",
    "Zestimate valuation tool drives organic traffic and user trust, functioning as a lead-generation hook.",
    "Expanding into iBuying and rental listings signals a shift toward owning more of the transaction, not just the discovery phase.",
    "Heavy reliance on agent ad spend creates exposure to real estate market cycles.",
    "Strong SEO and brand recognition make it the default entry point for property search, raising the bar for new entrants."
  ],
  "word_count": 842,
  "processing_time": "6.12s"
}
```

*This is the `competitor` mode — a strategic breakdown built for market research, not just a text summary.*

---

## 🚀 Features

| Feature | Details |
|---|---|
| **3 Summary Modes** | `quick` · `detailed` · `competitor` |
| **Smart Scraping** | Realistic browser headers, semantic HTML cleaning |
| **Rate Limiting** | 10 requests/min per IP with `Retry-After` header |
| **Retry Logic** | Auto-retries once on API timeout or failure |
| **Mock Mode** | Run and test without an API key |
| **Auto Docs** | Interactive Swagger UI at `/docs` |
| **Health Check** | `GET /health` endpoint for uptime monitoring |

---

## 🧠 Summary Modes Explained

### `quick`
A concise 1-2 paragraph overview with exactly **3 high-impact bullet points**.
Best for: fast research, content scanning.

### `detailed`
A comprehensive 3-4 paragraph deep analysis with **5-8 actionable insights**.
Best for: reports, due diligence, in-depth research.

### `competitor`
A business-focused strategic breakdown covering value proposition, target market, monetization model, and risks — with **4-6 strategic points**.
Best for: market research, competitive intelligence.

---

## 🛠️ Tech Stack

- **Python 3.9+**
- **[FastAPI](https://fastapi.tiangolo.com/)** — REST API framework
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** — HTML parsing & cleaning
- **[Google Gemini SDK](https://ai.google.dev/gemini-api/docs)** — Gemini AI summarization
- **[Pydantic](https://docs.pydantic.dev/)** — Input validation
- **[uvicorn](https://www.uvicorn.org/)** — ASGI server
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — Environment config

---

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Spetser-0/ai-web-summarizer-prod.git
cd ai-web-summarizer-prod
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
PORT=8000
HOST=127.0.0.1
ALLOW_MOCK_SUMMARY=false
```

> **No API key?** Set `ALLOW_MOCK_SUMMARY=true` to run in mock mode instantly.

### 4. Start the server

```bash
python api.py
```

Or with uvicorn directly:

```bash
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Open the docs

Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

---

## 📡 API Reference

### `POST /summarize`

Scrapes a URL and returns an AI-generated summary.

**Request body:**

```json
{
  "url": "https://example.com",
  "mode": "quick"
}
```

| Field | Type | Required | Options |
|---|---|---|---|
| `url` | string | ✅ | Any valid HTTP/HTTPS URL |
| `mode` | string | ❌ | `quick` · `detailed` · `competitor` (default: `quick`) |

**Response:**

```json
{
  "url": "string",
  "mode": "string",
  "summary": "string",
  "key_points": ["string"],
  "word_count": 0,
  "processing_time": "0.00s"
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| `400` | Invalid URL or bad request |
| `429` | Rate limit exceeded — check `Retry-After` header |
| `502` | Scraping failed or blocked by target site |
| `503` | Gemini API unavailable after retry |

---

### `GET /health`

Returns server status.

```json
{
  "status": "healthy",
  "timestamp": 1712345678.123
}
```

---

## 🧪 Run Tests

```bash
python test_app.py
```

Expected output:

```
Scraping and summarizing URL: https://news.ycombinator.com
Mode: quick
--------------------------------------------------
Scraped 566 words successfully.

Test Result (JSON):
{
  "url": "https://news.ycombinator.com",
  ...
}
```

> Note: `test_app.py` currently runs against Hacker News in `quick` mode by default — feel free to point it at a competitor URL with `mode="competitor"` to reproduce the Live Demo output above.

---

## 📁 Project Structure

```
ai-web-summarizer-prod/
├── scraper.py         # Web scraping engine
├── summarizer.py      # Google Gemini AI summarization + mock mode
├── api.py             # FastAPI server + rate limiting
├── test_app.py        # Manual test script
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
└── README.md          # You are here
```

---

## 🔒 Security Notes

- Never commit your `.env` file — it's in `.gitignore`
- API keys are loaded via environment variables only
- Rate limiting protects against abuse automatically

---

## 💡 Use Cases

- **Marketing agencies** — Analyze competitor websites in seconds
- **E-commerce stores** — Monitor market trends automatically
- **Researchers** — Summarize dozens of sources without reading each one
- **Developers** — Integrate AI summarization into any workflow via REST API

---

## 📄 License

MIT License — free to use, modify, and sell.

---

## 👤 Author

Built by a Python automation developer specializing in AI integration and web scraping.
Available for freelance projects on Freelancer.com.