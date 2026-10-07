"""The 50 most recent Trustpilot reviews for one company.

Reviews mode returns ONE company record per domain with the reviews nested
in its `reviews` list, so a bulk run stays one row per company.

Actor: https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/trustpilot-all-in-one-scraper").call(run_input={
    "scrapeType": "reviews",
    "companyUrls": ["www.revolut.com"],
    "sort": "recency",
    "maxReviewsPerCompany": 50,
})

for company in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"{company.get('companyName')}  TrustScore {company.get('trustScore')}  "
          f"({company.get('numberOfReviews')} reviews total)\n")
    for r in company.get("reviews") or []:
        mark = "verified" if r.get("isVerified") else "        "
        print(f"[{r.get('rating')}*] {mark} {(r.get('publishedDate') or '')[:10]}  "
              f"{r.get('reviewerCountry') or '--'}  {(r.get('reviewTitle') or '')[:70]}")
