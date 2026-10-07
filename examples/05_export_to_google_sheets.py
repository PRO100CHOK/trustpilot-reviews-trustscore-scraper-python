"""Weekly Trustpilot review monitor appended to a Google Sheet.

Setup:
  1. Google Cloud console -> create a service account -> download its JSON key.
  2. Save it as service_account.json next to this file (it is gitignored).
  3. Share the target spreadsheet with the service account's email address.
  4. List your own domain and the competitors you watch in DOMAINS.

Each run pulls the last 30 days of reviews and appends only review ids that
are not in the sheet yet, so support and marketing share one live feed.

Actor: https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python
"""
import os

import gspread
from apify_client import ApifyClient
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

SPREADSHEET = "Trustpilot review monitor"
WORKSHEET = "reviews"
DOMAINS = ["www.monzo.com", "www.starlingbank.com"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADER = ["review_id", "company", "published", "rating", "verified", "country",
          "title", "text", "company_reply", "url"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/trustpilot-all-in-one-scraper").call(run_input={
    "scrapeType": "reviews",
    "companyUrls": DOMAINS,
    "date": "last30days",
    "sort": "recency",
    "maxReviewsPerCompany": 200,
})

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
sheet = gspread.authorize(creds).open(SPREADSHEET)
try:
    ws = sheet.worksheet(WORKSHEET)
except gspread.WorksheetNotFound:
    ws = sheet.add_worksheet(WORKSHEET, rows=10000, cols=len(HEADER))
    ws.append_row(HEADER)

seen = set(ws.col_values(1)[1:])
rows = []
for company in client.dataset(run["defaultDatasetId"]).iterate_items():
    for r in company.get("reviews") or []:
        if r.get("reviewId") in seen:
            continue
        seen.add(r.get("reviewId"))
        rows.append([
            r.get("reviewId"), company.get("companyDomain"), r.get("publishedDate"),
            r.get("rating"), r.get("isVerified"), r.get("reviewerCountry"),
            (r.get("reviewTitle") or "")[:200], (r.get("reviewText") or "")[:1500],
            (r.get("replyMessage") or "")[:500], r.get("reviewUrl"),
        ])

if rows:
    ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Appended {len(rows)} new reviews to {SPREADSHEET}/{WORKSHEET}")
