import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


class NewsService:
    # ESPN sport/league path segments for the unofficial API
    ESPN_LEAGUES: dict[str, tuple[str, str]] = {
        "nfl": ("football", "nfl"),
        "nba": ("basketball", "nba"),
        "mlb": ("baseball", "mlb"),
        "tennis": ("tennis", "atp"),
        "golf": ("golf", "pga"),
    }

    def __init__(self):
        self.newsapi_key = os.environ.get("NEWSAPI_KEY")
        self.newsapi_url = "https://newsapi.org/v2/top-headlines"
        self.hn_url = "https://hacker-news.firebaseio.com/v0"
        self.espn_url = "https://site.api.espn.com/apis/site/v2/sports"

    def get_headlines(
        self, category: str, query: str | None = None, max_results: int = 8
    ) -> list[dict]:
        if not self.newsapi_key:
            raise ValueError("NEWSAPI_KEY not set")

        api_category = (
            category
            if category in {"general", "sports", "business", "entertainment"}
            else "general"
        )

        params: dict = {
            "apiKey": self.newsapi_key,
            "category": api_category,
            "pageSize": max_results,
            "language": "en",
        }

        if category not in {"world", "politics"}:
            params["country"] = "us"

        if query:
            params["q"] = query

        resp = requests.get(self.newsapi_url, params=params, timeout=10)
        resp.raise_for_status()

        return [
            {
                "title": a["title"],
                "source": a["source"]["name"],
                "description": a.get("description"),
                "url": a.get("url"),
                "published_at": a.get("publishedAt"),
            }
            for a in resp.json().get("articles", [])
            if a.get("title") and a["title"] != "[Removed]"
        ]

    def get_top_hn_stories(self, limit: int = 10, min_score: int = 50) -> list[dict]:
        top_ids = requests.get(f"{self.hn_url}/topstories.json", timeout=10).json()

        def fetch(story_id: int) -> dict | None:
            try:
                item = requests.get(f"{self.hn_url}/item/{story_id}.json", timeout=10).json()
                if not item or item.get("type") != "story":
                    return None
                return {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0),
                    "by": item.get("by"),
                }
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fetch, sid): sid for sid in top_ids[:50]}
            items = [f.result() for f in as_completed(futures)]

        return sorted(
            [i for i in items if i and i["score"] >= min_score],
            key=lambda x: x["score"],
            reverse=True,
        )[:limit]

    def get_espn_news(self, leagues: list[str], max_per_league: int = 5) -> list[dict]:
        def fetch_league(league: str) -> list[dict]:
            if league not in self.ESPN_LEAGUES:
                return []
            sport, slug = self.ESPN_LEAGUES[league]
            try:
                resp = requests.get(
                    f"{self.espn_url}/{sport}/{slug}/news",
                    params={"limit": max_per_league},
                    timeout=10,
                )
                resp.raise_for_status()
                return [
                    {
                        "league": league.upper(),
                        "title": a.get("headline"),
                        "description": a.get("description"),
                        "url": a.get("links", {}).get("web", {}).get("href"),
                        "published_at": a.get("published"),
                    }
                    for a in resp.json().get("articles", [])
                    if a.get("headline")
                ]
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=len(leagues)) as executor:
            results = list(executor.map(fetch_league, leagues))

        return [article for league_articles in results for article in league_articles]


news_service = NewsService()
