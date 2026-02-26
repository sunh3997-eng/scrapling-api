# 🕷️ Scrapling API

**Turn any website into structured data — one HTTP request.**

A production-ready REST API wrapper around [Scrapling](https://github.com/D4Vinci/Scrapling), the fastest adaptive web scraping library for Python. Bypass Cloudflare, scrape JS-heavy pages, and extract structured data with CSS/XPath selectors — all via a simple HTTP API.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
[![Docker Pulls](https://img.shields.io/docker/pulls/placeholder/scrapling-api)](https://hub.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Why Scrapling API?

| Feature | Scrapling API | Apify | ScrapingBee | SerpAPI |
|---------|:---:|:---:|:---:|:---:|
| Self-hosted | ✅ | ❌ | ❌ | ❌ |
| Cloudflare bypass | ✅ | ✅ | ✅ | ✅ |
| Adaptive selectors | ✅ | ❌ | ❌ | ❌ |
| Free to use | ✅ | Limited | Limited | Limited |
| Open source | ✅ | ❌ | ❌ | ❌ |
| CSS + XPath | ✅ | ✅ | ✅ | ❌ |

**Self-host once, scrape forever. No per-request pricing.**

---

## 🚀 Quick Start

### Option 1 — Docker (recommended)

```bash
git clone https://github.com/YOUR_USERNAME/scrapling-api
cd scrapling-api

# Optional: set an API key for protection
echo "SCRAPLING_API_KEY=your-secret-key" > .env

docker-compose up -d
```

API is live at `http://localhost:8000`

### Option 2 — Python

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 📖 API Reference

Interactive docs at **`http://localhost:8000/docs`**

### `POST /scrape`

Scrape a URL and optionally extract elements.

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "url": "https://news.ycombinator.com",
    "mode": "fetch",
    "selector": ".titleline > a",
    "extract": "text"
  }'
```

**Response:**
```json
{
  "url": "https://news.ycombinator.com",
  "status_code": 200,
  "mode": "fetch",
  "data": [
    "Show HN: I built a minimal text-to-speech tool",
    "Nvidia quarterly profit hits $43 billion",
    "..."
  ],
  "element_count": 30,
  "elapsed_ms": 412
}
```

### Scrape modes

| Mode | Speed | Use case |
|------|-------|----------|
| `fetch` | ⚡ ~300ms | Most websites, static HTML, APIs |
| `stealth` | 🐢 ~3-8s | Cloudflare-protected sites, bot detection |
| `dynamic` | 🐢 ~2-5s | SPAs, infinite scroll, React/Vue/Angular |

### `POST /extract`

Extract multiple fields at once — perfect for product pages, listings, etc.

```bash
curl -X POST "http://localhost:8000/extract?url=https://example-shop.com/product/123&mode=fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "h1.product-title",
    "price": ".price-tag",
    "rating": ".star-rating",
    "stock": "#stock-status"
  }'
```

**Response:**
```json
{
  "url": "https://example-shop.com/product/123",
  "data": {
    "title": ["Wireless Headphones Pro"],
    "price": ["$49.99"],
    "rating": ["4.5 / 5"],
    "stock": ["In Stock"]
  }
}
```

---

## 💡 Use Cases

- **Price monitoring** — Track competitor prices across e-commerce sites
- **Lead generation** — Extract contacts from directories and listings
- **News aggregation** — Build custom RSS feeds from any website
- **Market research** — Collect data from job boards, review sites, forums
- **AI training data** — Batch-collect clean text from the web
- **Real estate** — Scrape listing prices, addresses, availability

---

## 🔒 Authentication

Set `SCRAPLING_API_KEY` in your environment. Pass it via the `X-API-Key` header.

```bash
export SCRAPLING_API_KEY="your-secret-key"
```

Leave it empty to run without auth (development only).

---

## ⚙️ Configuration

| Env Variable | Default | Description |
|---|---|---|
| `SCRAPLING_API_KEY` | `""` | API key (empty = no auth) |
| `PORT` | `8000` | Server port |

---

## 🏗️ Project Structure

```
scrapling-api/
├── app/
│   └── main.py          # FastAPI app + all endpoints
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 📦 Deploy in 1 click

### Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Render
1. Fork this repo
2. New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### VPS / Self-hosted
```bash
docker-compose up -d
```

---

## 🙏 Credits

Built on top of [Scrapling](https://github.com/D4Vinci/Scrapling) by [@D4Vinci](https://github.com/D4Vinci) — the best adaptive web scraping library for Python.

---

## 📄 License

MIT — free to use, modify, and deploy.
