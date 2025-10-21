from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


@dataclass
class NewsArticle:
    source: str
    headline: str
    url: str
    published_at: datetime
    summary: Optional[str] = None


class NewsFetcher:
    """Lightweight wrapper around Finnhub and NewsAPI for headline retrieval."""

    def __init__(
        self,
        lookback_hours: int = 24,
        company_headlines: int = 1,
        general_headlines: int = 3,
        refresh_minutes: int = 60,
    ) -> None:
        self._finnhub_key = os.getenv("FINNHUB_API_KEY")
        self._newsapi_key = os.getenv("NEWSAPI_KEY")
        self._lookback = timedelta(hours=max(lookback_hours, 1))
        self._company_headlines = max(company_headlines, 0)
        self._general_headlines = max(general_headlines, 0)
        self._refresh = timedelta(minutes=max(refresh_minutes, 1))
        self._company_cache: Dict[str, tuple[datetime, List[NewsArticle]]] = {}
        self._general_cache: Optional[tuple[datetime, List[NewsArticle]]] = None

    def get_company_headlines(self, symbols: List[str]) -> Dict[str, List[NewsArticle]]:
        now = datetime.now(timezone.utc)
        results: Dict[str, List[NewsArticle]] = {}
        if not self._finnhub_key or self._company_headlines <= 0:
            return results

        for symbol in symbols:
            cached = self._company_cache.get(symbol)
            if cached and now - cached[0] < self._refresh:
                results[symbol] = cached[1][: self._company_headlines]
                continue
            articles = self._fetch_finnhub_company_news(symbol)
            if articles:
                self._company_cache[symbol] = (now, articles)
                results[symbol] = articles[: self._company_headlines]
        return results

    def get_market_headlines(self) -> List[NewsArticle]:
        now = datetime.now(timezone.utc)
        if not self._newsapi_key or self._general_headlines <= 0:
            return []

        cached = self._general_cache
        if cached and now - cached[0] < self._refresh:
            return cached[1][: self._general_headlines]

        articles = self._fetch_newsapi_headlines()
        if articles:
            self._general_cache = (now, articles)
        return articles[: self._general_headlines]

    def _fetch_finnhub_company_news(self, symbol: str) -> List[NewsArticle]:
        if not self._finnhub_key:
            return []
        end = datetime.utcnow()
        start = end - self._lookback
        params = {
            "symbol": symbol,
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
            "token": self._finnhub_key,
        }
        try:
            resp = requests.get(
                "https://finnhub.io/api/v1/company-news",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # pragma: no cover - network failure paths
            logger.warning("Finnhub news fetch failed for %s: %s", symbol, exc)
            return []
        articles: List[NewsArticle] = []
        for item in payload or []:
            published = datetime.fromtimestamp(
                item.get("datetime", 0), tz=timezone.utc
            )
            articles.append(
                NewsArticle(
                    source=(item.get("source") or "Finnhub"),
                    headline=item.get("headline") or "",
                    url=item.get("url") or "",
                    published_at=published,
                    summary=item.get("summary"),
                )
            )
        return sorted(articles, key=lambda a: a.published_at, reverse=True)

    def _fetch_newsapi_headlines(self) -> List[NewsArticle]:
        if not self._newsapi_key:
            return []
        params = {
            "category": "business",
            "language": "en",
            "pageSize": max(self._general_headlines, 3),
        }
        headers = {"X-Api-Key": self._newsapi_key}
        try:
            resp = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params=params,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # pragma: no cover - network failure paths
            logger.warning("NewsAPI fetch failed: %s", exc)
            return []
        articles: List[NewsArticle] = []
        for item in payload.get("articles", []):
            published_raw = item.get("publishedAt")
            try:
                published = (
                    datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                    if published_raw
                    else datetime.now(timezone.utc)
                )
            except Exception:
                published = datetime.now(timezone.utc)
            articles.append(
                NewsArticle(
                    source=(item.get("source") or {}).get("name", "NewsAPI"),
                    headline=item.get("title") or "",
                    url=item.get("url") or "",
                    published_at=published,
                    summary=item.get("description"),
                )
            )
        return sorted(articles, key=lambda a: a.published_at, reverse=True)
