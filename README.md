# Trustpilot Reviews & TrustScore Scraper in Python

> Export Trustpilot reviews, TrustScores, star distributions, reply rates and company contacts into Python — no Trustpilot business account, no API approval.

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-blue)](https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A working Python project for the [Trustpilot Reviews Scraper API on Apify](https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python). It shows how to benchmark competitors' reputations, mine complaints, build lead lists from Trustpilot categories and keep a live review feed in Google Sheets.

## What this does

Trustpilot's official APIs are meant for businesses managing their own profile: you need a business account and an API key, and you only see your own data. If you want to read a competitor's reviews, score a list of vendors or export a whole category, there is no official route.

The actor behind this repo works as an **unofficial Trustpilot API**. It reads the public pages and returns clean JSON in six modes:

| `scrapeType` | Input field | What comes back |
|---|---|---|
| `reviews` | `companyUrls` | one company record with its reviews nested in a `reviews` list |
| `company` | `companyUrls` | TrustScore, stars, 1–5 star counts, categories and category ranks, email, phone, address, claim status, verification badges, reply behaviour |
| `transparency` | `companyUrls` | star distribution, review-language breakdown, reply rate, average days to reply, negative reviews answered |
| `search` | `searchTerms` | companies matching a brand name or keyword, localised by `country` |
| `category` | `categories` | every company in a Trustpilot category, with website, email, phone and address |
| `userReviews` | `userUrls` | one reviewer's profile with all their reviews |

Each review record carries the rating, title and full text, language, experienced/published/updated dates, verification level and source, likes, reviewer name, country and review count, and the company's reply with its dates.

## Past the 200-review limit

Anonymous visitors to Trustpilot can page through at most 200 reviews for any filter combination. Set `maxReviewsPerCompany` above 200 and the actor sweeps each star rating separately, merges the results and removes duplicates by review id, which raises the ceiling to roughly 1,000 reviews per company.

## Chain discovery into detail

`enrichWith` turns a search, category or company run into one nested row per company. Add `company`, `transparency` and/or `reviews`, and the profile, the analytics block and the reviews are fetched for every company found and attached to the same record. Each nested item is still billed at its own event price, so you pay only for what you ask for.

## Use cases

- **Competitor benchmarking** — compare TrustScore, negative-review share and reply speed across a whole niche. `main.py` does this for four VPN brands.
- **Complaint mining** — pull only one- and two-star reviews from the last three months to see what is breaking for a rival's customers right now.
- **Vendor and partner vetting** — check claim status, verification badges, paid-feature use and how often a company answers criticism.
- **B2B lead generation** — export a category for one country with each company's public email and phone.
- **Review monitoring** — append new reviews of your brand to a Google Sheet every week so support sees them fast.
- **Local market research** — filter reviews by language (`de`, `fr`, `it`…) to hear one market at a time.
- **Sentiment and NLP datasets** — rated review text with dates, language and verification flags, ready for training or evaluation.

## Requirements

- Python **3.10+**
- A free [Apify account](https://console.apify.com/sign-up) — $5 of usage credit every month on the free plan
- No Trustpilot account or business API key

## Quick start

```bash
git clone https://github.com/pro100chok/trustpilot-reviews-trustscore-scraper-python.git
cd trustpilot-reviews-trustscore-scraper-python
pip install -r requirements.txt
cp .env.example .env
# add your APIFY_API_TOKEN to .env
python main.py
```

`main.py` runs a two-step reputation benchmark. First it pulls transparency analytics for every competitor and ranks them by share of one- and two-star ratings, reply rate and days to reply. Then it collects each competitor's recent negative reviews, counts how many got a company reply, prints the words unhappy customers repeat most, and saves `output.json` plus a one-row-per-review `output.csv`.

## How it works

You send a JSON input to the actor through the official `apify-client` package; the run executes on Apify's infrastructure and your script reads the dataset when it finishes. Trustpilot's bot protection, proxies, retries and pagination are handled inside the actor, and `maxConcurrency` (1–10) controls how many companies are processed in parallel. Review filters map directly to Trustpilot's own: `stars`, `language`, `date`, `verifiedOnly`, `repliesOnly`, `reviewSearchQuery` and `sort`.

## Example: unanswered complaints that mention refunds

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])
run = client.actor("pro100chok/trustpilot-all-in-one-scraper").call(run_input={
    "scrapeType": "reviews",
    "companyUrls": ["www.ryanair.com"],
    "stars": ["1", "2"],
    "reviewSearchQuery": "refund",
    "date": "last6months",
    "maxReviewsPerCompany": 200,
})

for company in client.dataset(run["defaultDatasetId"]).iterate_items():
    for r in company.get("reviews", []):
        if not r.get("replyMessage"):
            print(r["rating"], r["publishedDate"][:10], r["reviewTitle"])
```

## Example output

A nested review from `reviews` mode (trimmed):

```json
{
  "reviewId": "66f1c2a9b0e4d52a1c3e8f71",
  "reviewUrl": "https://www.trustpilot.com/reviews/66f1c2a9b0e4d52a1c3e8f71",
  "rating": 2,
  "reviewTitle": "Refund took six weeks",
  "reviewText": "The product works, but getting my money back was a nightmare...",
  "language": "en",
  "experiencedDate": "2026-08-30T00:00:00.000Z",
  "publishedDate": "2026-09-03T14:21:08.000Z",
  "isVerified": true,
  "verificationLevel": "verified",
  "likes": 3,
  "reviewerName": "Daniel K.",
  "reviewerCountry": "GB",
  "reviewerNumberOfReviews": 7,
  "replyMessage": "Hi Daniel, we're sorry for the delay...",
  "replyPublishedDate": "2026-09-04T09:02:11.000Z"
}
```

The parent company record holds `companyName`, `companyDomain`, `trustScore`, `stars`, `numberOfReviews`, `ratingOneStar`…`ratingFiveStars`, `primaryCategory`, `email`, `phone`, `replyPercentage`, `averageDaysToReply`, `reviews` and `reviewsCount`.

## Input parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `scrapeType` | string | `reviews` | `reviews`, `company`, `transparency`, `search`, `category`, `userReviews` |
| `companyUrls` | string[] | — | Trustpilot review URLs or bare domains (`nordvpn.com`) |
| `searchTerms` | string[] | — | Brand names or keywords for `search` |
| `categories` | string[] | — | Category ids or URLs for `category` (e.g. `bank`) |
| `userUrls` | string[] | — | Reviewer profile URLs or ids for `userReviews` |
| `maxReviewsPerCompany` | integer | `200` | Above 200 triggers the per-star sweep (up to ~1,000) |
| `maxResults` | integer | `100` | Companies per search term or category |
| `sort` | string | `recency` | `recency` or `relevancy` |
| `stars` | string[] | all | Any of `1`–`5` |
| `language` | string | all | ISO code such as `en`, `de`, `it` |
| `date` | string | `all` | `last30days`, `last3months`, `last6months`, `last12months` |
| `verifiedOnly` | boolean | `false` | Only verified reviews |
| `repliesOnly` | boolean | `false` | Only reviews the company replied to |
| `reviewSearchQuery` | string | — | Only reviews containing this keyword |
| `country` | string | `US` | Two-letter code for search and category results |
| `enrichWith` | string[] | — | `company`, `transparency`, `reviews` nested per company |
| `maxConcurrency` | integer | `4` | Companies in parallel (1–10) |

## More examples

| File | Demonstrates |
|---|---|
| `examples/01_basic_usage.py` | The 50 newest reviews for one company. |
| `examples/02_company_profile_trustscore.py` | TrustScore, star counts, badges, reply behaviour and contacts for three vendors. |
| `examples/03_category_leads_with_emails.py` | A Trustpilot category turned into a CSV of companies with email and phone. |
| `examples/04_export_to_csv.py` | Up to 800 reviews to CSV with a monthly rating and reply-rate trend in pandas. |
| `examples/05_export_to_google_sheets.py` | Weekly review feed for your brand and rivals in Google Sheets, no duplicates. |

## Ready-made tasks

Public presets of the same actor — open one, swap in your company and run:

- [Export All Trustpilot Reviews for a Company](https://apify.com/pro100chok/trustpilot-export-company-reviews?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)
- [Mine One and Two Star Trustpilot Complaints](https://apify.com/pro100chok/trustpilot-negative-reviews-analysis?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)
- [Get TrustScore and Company Profile Data](https://apify.com/pro100chok/trustpilot-company-profile-trustscore?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)
- [Scan a Whole Trustpilot Category for Competitors](https://apify.com/pro100chok/trustpilot-category-competitor-scan?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)
- [Find Trustpilot Reviews Mentioning a Keyword](https://apify.com/pro100chok/trustpilot-keyword-search-in-reviews?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)
- [Export Verified Reviews That Got a Company Reply](https://apify.com/pro100chok/trustpilot-verified-reviews-with-replies?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python)

## Pricing

Pay per event. Prices are the free plan, then Gold and higher:

| Event | Free plan | Gold+ |
|---|---|---|
| Review | $0.001 | $0.0004 |
| Company profile | $0.005 | $0.003 |
| Transparency & analytics record | $0.008 | $0.003 |
| Search or category result | $0.002 | $0.0014 |

1,000 reviews cost $1.00 on the free plan and $0.40 on Gold; a run start is $0.00005 per GB of memory.

## FAQ

**Do I need a Trustpilot API key?**
No. Only an Apify API token. The actor reads the same public pages any visitor sees.

**How many reviews can I get for one company?**
Up to 200 per filter combination, or roughly 1,000 when `maxReviewsPerCompany` is above 200 and the actor sweeps each star rating.

**Can I get a company's email and phone?**
Yes, when the company lists them on Trustpilot. They appear on `company` records and on `search` and `category` results.

**Why does reviews mode return one row per company?**
Reviews are nested in the company record so a bulk run stays tidy. Flatten them with one list comprehension, as in `examples/04_export_to_csv.py`.

**Can I filter to one country's reviews?**
Filter by `language`; each review also carries `reviewerCountry` for finer filtering in pandas.

**Is scraping Trustpilot legal?**
The actor collects only publicly visible data without logging in. Reviewer names are personal data under GDPR, so store and process them responsibly.

## Related actors

- [G2 Scraper](https://apify.com/pro100chok/g2-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python) — B2B software reviews and ratings for the same vendors.
- [Google Maps Scraper](https://apify.com/pro100chok/google-maps-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python) — local business reviews, photos and contacts.
- [TripAdvisor Scraper](https://apify.com/pro100chok/tripadvisor-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python) — hotel and restaurant reviews for travel brands.
- [Website Contact Scraper](https://apify.com/pro100chok/extract-emails?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python) — emails, phones and socials from each company's own website.

## License

MIT — see [LICENSE](LICENSE).

---

Built on the [Trustpilot Reviews Scraper API](https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python) Apify actor by pro100chok.
