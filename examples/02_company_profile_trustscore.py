"""Trustpilot company profiles: TrustScore, star split, contacts and badges.

Useful for vendor vetting: in one run you see the score, how the ratings are
distributed, whether the profile is claimed, whether the company pays for
Trustpilot features or uses AI replies, and its public email and phone.

Actor: https://apify.com/pro100chok/trustpilot-all-in-one-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=trustpilot-reviews-trustscore-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

VENDORS = ["www.shopify.com", "www.wix.com", "www.squarespace.com"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/trustpilot-all-in-one-scraper").call(run_input={
    "scrapeType": "company",
    "companyUrls": VENDORS,
})

for c in client.dataset(run["defaultDatasetId"]).iterate_items():
    stars = [c.get(k) or 0 for k in ("ratingOneStar", "ratingTwoStars", "ratingThreeStars",
                                     "ratingFourStars", "ratingFiveStars")]
    print(f"\n{c.get('companyName')}  ({c.get('companyDomain')})")
    print(f"  TrustScore {c.get('trustScore')}  stars {c.get('stars')}  "
          f"reviews {c.get('numberOfReviews')}")
    print(f"  1-5 star counts: {stars}")
    print(f"  category: {c.get('primaryCategory')}  country: {c.get('countryCode')}")
    print(f"  claimed: {c.get('isClaimed')}  paid features: {c.get('isUsingPaidFeatures')}  "
          f"AI replies: {c.get('isUsingAIResponses')}")
    print(f"  replies to {c.get('replyPercentage')}% of reviews, "
          f"avg {c.get('averageDaysToReply')} days")
    print(f"  contact: {c.get('email') or '-'} / {c.get('phone') or '-'} / {c.get('city') or '-'}")
