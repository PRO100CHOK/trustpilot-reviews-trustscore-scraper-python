"""Trustpilot Reviews + TrustScore Scraper — competitor reputation benchmark.

Use case: you sell in a crowded market (here: VPN providers) and want to know
which competitor is most exposed. The script
  1. pulls Trustpilot analytics for every competitor: TrustScore, the 1-5
     star split, how often and how fast each company replies to reviews,
  2. collects each competitor's recent one- and two-star reviews,
  3. ranks the competitors by share of negative reviews and prints the words
     their unhappy customers repeat most,
  4. saves output.json (everything) and output.csv (one row per review).

Run:
    pip install -r requirements.txt
    cp .env.example .env
    python main.py

Actor: https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

ACTOR_ID = "pro100chok/trustpilot-all-in-one-scraper"
COMPETITORS = ["nordvpn.com", "expressvpn.com", "surfshark.com", "protonvpn.com"]
NEGATIVE_REVIEWS_PER_COMPANY = 100

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "you", "your", "not", "but",
    "have", "has", "are", "was", "were", "can", "they", "their", "them", "when",
    "what", "there", "would", "could", "just", "from", "about", "will", "then",
    "than", "been", "also", "some", "only", "after", "because", "don't", "even",
    "still", "never", "said", "told", "again", "very", "which", "into", "being",
    "company", "service", "vpn",
}


def themes(texts: list[str], n: int = 10) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for text in texts:
        for word in re.findall(r"[a-z][a-z'-]{3,}", (text or "").lower()):
            if word not in STOPWORDS:
                counter[word] += 1
    return counter.most_common(n)


def run_actor(client: ApifyClient, run_input: dict, label: str) -> list[dict]:
    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=1800)
    except ApifyApiError as exc:
        sys.exit(f"{label} failed: {exc}")
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def share(part: int | None, total: int | None) -> float:
    return round(100 * (part or 0) / total, 1) if total else 0.0


def main() -> int:
    load_dotenv()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN missing — copy .env.example to .env first.")
    client = ApifyClient(token)
    out = Path(__file__).parent

    # Step 1: reputation analytics for every competitor
    print(f"Step 1/2 — Trustpilot analytics for {len(COMPETITORS)} companies")
    analytics = run_actor(client, {
        "scrapeType": "transparency",
        "companyUrls": COMPETITORS,
        "maxConcurrency": 4,
    }, "Analytics step")

    for a in analytics:
        total = a.get("totalRatedReviews") or a.get("numberOfReviews")
        negative = (a.get("ratingOneStar") or 0) + (a.get("ratingTwoStars") or 0)
        a["negativeShare"] = share(negative, total)
    analytics.sort(key=lambda a: -a["negativeShare"])

    print(f"  {'company':<18} {'TrustScore':>10} {'reviews':>9} {'1-2 star':>9} "
          f"{'replies':>8} {'days':>5}")
    for a in analytics:
        print(f"  {a.get('companyDomain', '?'):<18} {a.get('trustScore') or '-':>10} "
              f"{a.get('numberOfReviews') or 0:>9} {a['negativeShare']:>8}% "
              f"{a.get('replyPercentage') or 0:>7}% {a.get('averageDaysToReply') or '-':>5}")

    # Step 2: what the unhappy customers actually say
    print(f"\nStep 2/2 — up to {NEGATIVE_REVIEWS_PER_COMPANY} recent 1-2 star reviews each")
    companies = run_actor(client, {
        "scrapeType": "reviews",
        "companyUrls": COMPETITORS,
        "stars": ["1", "2"],
        "date": "last3months",
        "sort": "recency",
        "maxReviewsPerCompany": NEGATIVE_REVIEWS_PER_COMPANY,
        "maxConcurrency": 4,
    }, "Reviews step")

    rows: list[dict] = []
    for company in companies:
        reviews = company.get("reviews") or []
        replied = sum(1 for r in reviews if r.get("replyMessage"))
        print(f"\n  {company.get('companyName')} — {len(reviews)} negative reviews, "
              f"{replied} answered by the company")
        for word, count in themes([f"{r.get('reviewTitle')} {r.get('reviewText')}"
                                   for r in reviews]):
            print(f"      {count:>3}x  {word}")
        for r in reviews:
            rows.append({"company": company.get("companyDomain"), **r})

    (out / "output.json").write_text(
        json.dumps({"analytics": analytics, "companies": companies},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    fields = ["company", "reviewId", "rating", "publishedDate", "language",
              "reviewerCountry", "isVerified", "reviewTitle", "reviewText",
              "replyMessage", "reviewUrl"]
    with (out / "output.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved output.json and output.csv ({len(rows)} reviews)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
