"""
Scrapling API — Turn any website into structured data via REST API.
Built on top of Scrapling: https://github.com/D4Vinci/Scrapling
"""

import time
from typing import Optional, Literal, Any
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os

app = FastAPI(
    title="Scrapling API",
    description="Universal web scraping API — fetches any site, bypasses anti-bot, extracts structured data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth ────────────────────────────────────────────────────────────────────

API_KEY = os.getenv("SCRAPLING_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_key(key: str = Security(api_key_header)):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return key

# ─── Schemas ─────────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="Target URL to scrape")
    mode: Literal["fetch", "stealth", "dynamic"] = Field(
        "fetch",
        description=(
            "fetch = fast HTTP (impersonates browser TLS)\n"
            "stealth = headless browser, bypasses Cloudflare\n"
            "dynamic = full browser with JS execution"
        ),
    )
    selector: Optional[str] = Field(None, description="CSS selector to extract elements")
    xpath: Optional[str] = Field(None, description="XPath selector to extract elements")
    extract: Literal["text", "html", "all"] = Field(
        "text", description="What to extract from matched elements"
    )
    headless: bool = Field(True, description="Run browser in headless mode (stealth/dynamic only)")
    wait_network_idle: bool = Field(False, description="Wait for network to be idle before extracting")
    timeout: int = Field(30, ge=5, le=120, description="Request timeout in seconds")
    proxy: Optional[str] = Field(None, description="Proxy URL (e.g. http://user:pass@host:port)")

class ScrapeResult(BaseModel):
    url: str
    status_code: int
    mode: str
    data: Any
    element_count: Optional[int] = None
    elapsed_ms: int

class HealthResponse(BaseModel):
    status: str
    version: str

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/scrape", response_model=ScrapeResult, tags=["Scraping"])
def scrape(req: ScrapeRequest, _: str = Depends(verify_key)):
    """
    Universal scrape endpoint.

    - **fetch**: Lightning-fast HTTP with browser TLS impersonation. Best for most sites.
    - **stealth**: Headless real browser. Bypasses Cloudflare Turnstile / JS challenges.
    - **dynamic**: Full Playwright browser. Best for SPAs and heavily JS-driven pages.

    Optionally pass a **CSS selector** or **XPath** to extract specific elements.
    """
    start = time.monotonic()

    try:
        page = _fetch_page(req)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {str(e)}")

    status_code = getattr(page, "status", 200)

    # Extract data
    if req.selector or req.xpath:
        try:
            elements = (
                page.css(req.selector) if req.selector else page.xpath(req.xpath)
            )
            if req.extract == "text":
                data = [_el_text(el) for el in elements if _el_text(el)]
            elif req.extract == "html":
                data = [str(el) for el in elements]
            else:  # "all"
                data = [
                    {
                        "text": _el_text(el),
                        "html": str(el),
                        "attribs": dict(el.attrib) if hasattr(el, "attrib") and el.attrib else {},
                    }
                    for el in elements
                ]
            element_count = len(elements)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Selector error: {str(e)}")
    else:
        # No selector — return full page text
        if hasattr(page, "get_all_text"):
            data = page.get_all_text(separator="\n", ignore_tags=("script", "style"))
        elif hasattr(page, "text"):
            data = page.text
        else:
            data = str(page)
        element_count = None

    elapsed_ms = int((time.monotonic() - start) * 1000)
    return ScrapeResult(
        url=req.url,
        status_code=status_code,
        mode=req.mode,
        data=data,
        element_count=element_count,
        elapsed_ms=elapsed_ms,
    )


@app.post("/extract", tags=["Scraping"])
def extract_multi(
    url: str,
    selectors: dict[str, str],
    mode: Literal["fetch", "stealth", "dynamic"] = "fetch",
    _: str = Depends(verify_key),
):
    """
    Extract multiple fields in one request using a dict of {field_name: css_selector}.

    Example:
    ```json
    {
      "url": "https://example.com",
      "selectors": {
        "title": "h1",
        "price": ".price",
        "description": ".product-desc"
      }
    }
    ```
    """
    try:
        page = _fetch_page(ScrapeRequest(url=url, mode=mode))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {str(e)}")

    result = {}
    for field, sel in selectors.items():
        try:
            elements = page.css(sel)
            texts = [_el_text(el) for el in elements if _el_text(el)]
            result[field] = texts or None
        except Exception:
            result[field] = None

    return {"url": url, "data": result}


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _el_text(el) -> Optional[str]:
    """
    Safely extract text from a Scrapling element.
    - Adaptor (DOM node): use .text
    - TextHandler (text/attr node from XPath): use str()
    """
    if hasattr(el, "text"):
        return el.text or None
    val = str(el).strip()
    return val if val else None


def _fetch_page(req: ScrapeRequest):
    """Route to the correct Scrapling fetcher based on mode."""
    kwargs: dict = {"timeout": req.timeout * 1000}  # Scrapling uses ms
    if req.proxy:
        kwargs["proxy"] = req.proxy

    if req.mode == "fetch":
        from scrapling.fetchers import Fetcher
        return Fetcher.get(req.url, stealthy_headers=True, **kwargs)

    elif req.mode == "stealth":
        from scrapling.fetchers import StealthyFetcher
        return StealthyFetcher.fetch(
            req.url,
            headless=req.headless,
            network_idle=req.wait_network_idle,
            **kwargs,
        )

    elif req.mode == "dynamic":
        from scrapling.fetchers import DynamicFetcher
        return DynamicFetcher.fetch(
            req.url,
            headless=req.headless,
            network_idle=req.wait_network_idle,
            **kwargs,
        )

    raise ValueError(f"Unknown mode: {req.mode}")
