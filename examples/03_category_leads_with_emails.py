"""B2B lead list from a Trustpilot category: companies with email and phone.

Category mode lists every company in a Trustpilot category for one country,
with website, email, phone, address, TrustScore and review count. Adding
"company" to enrichWith nests the full profile into each row as well.

Actor: https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python
"""
import csv
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

CATEGORY = "insurance_agency"   # a category id or https://www.trustpilot.com/categories/<id>
COUNTRY = "GB"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/trustpilot-all-in-one-scraper").call(run_input={
    "scrapeType": "category",
    "categories": [CATEGORY],
    "country": COUNTRY,
    "maxResults": 60,
})

leads = [c for c in client.dataset(run["defaultDatasetId"]).iterate_items()
         if c.get("email") or c.get("phone")]
leads.sort(key=lambda c: c.get("numberOfReviews") or 0, reverse=True)

fields = ["companyName", "websiteUrl", "email", "phone", "city", "trustScore",
          "numberOfReviews", "primaryCategory", "companyUrl"]
with open("leads.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(leads)

for c in leads[:15]:
    print(f"{c.get('trustScore') or '-':>4}  {c.get('numberOfReviews') or 0:>6}  "
          f"{(c.get('companyName') or '')[:30]:<30} {c.get('email') or '-':<32} {c.get('phone') or '-'}")
print(f"\n{len(leads)} companies with contacts saved to leads.csv")
