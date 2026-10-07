"""Export up to ~1,000 Trustpilot reviews to CSV and chart the monthly rating trend.

Trustpilot shows anonymous visitors at most 200 reviews per filter. With
maxReviewsPerCompany above 200 the actor sweeps each star rating separately
and merges the results, de-duplicated by review id.

Actor: https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python
"""
import os

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

DOMAIN = "www.booking.com"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/trustpilot-all-in-one-scraper").call(run_input={
    "scrapeType": "reviews",
    "companyUrls": [DOMAIN],
    "maxReviewsPerCompany": 800,
    "date": "last12months",
    "sort": "recency",
})

companies = list(client.dataset(run["defaultDatasetId"]).iterate_items())
reviews = [r for c in companies for r in (c.get("reviews") or [])]
if not reviews:
    raise SystemExit(f"No reviews returned for {DOMAIN}.")

df = pd.DataFrame(reviews)
df["publishedDate"] = pd.to_datetime(df["publishedDate"], errors="coerce", utc=True)
df["month"] = df["publishedDate"].dt.strftime("%Y-%m")
df["hasReply"] = df.get("replyMessage", pd.Series(index=df.index, dtype=object)).notna()

cols = ["reviewId", "publishedDate", "rating", "language", "reviewerCountry",
        "isVerified", "hasReply", "reviewTitle", "reviewText", "reviewUrl"]
df[[c for c in cols if c in df.columns]].to_csv("output.csv", index=False)

trend = df.groupby("month").agg(reviews=("rating", "size"),
                                avg_rating=("rating", "mean"),
                                reply_rate=("hasReply", "mean"))
trend["avg_rating"] = trend["avg_rating"].round(2)
trend["reply_rate"] = (trend["reply_rate"] * 100).round(1)
print(trend.to_string())
print("\nRating distribution:")
print(df["rating"].value_counts().sort_index().to_string())
print(f"\nSaved {len(df)} reviews to output.csv")
