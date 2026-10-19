"""Agent 1: searches Amazon, Costco and Best Buy for price errors and unusually deep electronics sales."""

from __future__ import annotations

from datetime import date

from .runner import run_agent, web_tools
from .schemas import ScoutReport

SYSTEM = """You are the Scout for Jelectronics, a site that tracks price errors and exceptional sales on consumer electronics.

Hunt across Amazon (amazon.com), Costco (costco.com) and Best Buy (bestbuy.com) for deals on laptops, tablets, phones, monitors, TVs, headphones, cameras, gaming hardware and smart home gear.

What counts as a find:
- Price errors / pricing glitches (e.g. a $1,299 laptop listed at $129).
- Flash sales, Deal of the Day, clearance or open-box markdowns that are at least ~25% below the item's usual selling price, or an all-time low.
- Skip routine 5-15% discounts, refurbished items from unknown third-party sellers, and accessories under $30.

How to work:
- Cast a wide net: search deal communities (Slickdeals, Reddit r/buildapcsales, r/deals, r/PriceErrors), price trackers (CamelCamelCamel, Keepa summaries), and the retailers' own deal pages.
- Always trace a find back to the retailer's own product page URL; never submit a forum or aggregator link as the deal URL.
- Record the regular price from a credible reference (the retailer's "was" price, a price tracker's typical price, or MSRP) and say which in the evidence.
- For image_url, use the retailer's product image if you saw it (e.g. m.media-amazon.com, pisces.bbystatic.com, costco-static.com); otherwise leave it empty. Do not invent URLs.
- Aim for 10-25 candidates spread across retailers and categories. Quality over quantity: the Verifier will reject anything stale or wrong.
"""


def run(seen_ids: list[str]) -> ScoutReport:
    prompt = (
        f"Today is {date.today():%A, %B %d, %Y}. Find today's best electronics price errors and sales.\n\n"
        "Deals already on the site (re-submit one only if it is still live and you have fresher details):\n"
        + ("\n".join(f"- {i}" for i in seen_ids) or "(none)")
    )
    return run_agent(
        name="scout",
        system=SYSTEM,
        prompt=prompt,
        output=ScoutReport,
        tools=web_tools(search_uses=40, fetch_uses=25),
        effort="high",
    )
