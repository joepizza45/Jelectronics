"""Agent 3: merges scout + verifier output into the site's data files and writes the day's editorial copy."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .runner import run_agent
from .schemas import Candidate, PublishedDeal, PublisherReport, Verification

DATA_DIR = Path(__file__).resolve().parent.parent / "site" / "data"
MIN_CONFIDENCE = 60

SYSTEM = """You are the Publisher for Jelectronics, a clean, trustworthy electronics-deals site. You receive deals that have already been verified.

Write in a calm, professional voice: no hype words like "insane" or "INSANE", no emoji, no exclamation marks. Headlines lead with the product and the price, e.g. "MacBook Air M4 13-inch drops to $749 at Best Buy".
Pick one featured deal: favor genuine price errors and the largest absolute savings with high confidence.
"""


def _load_previous() -> dict[str, dict]:
    path = DATA_DIR / "deals.json"
    if not path.exists():
        return {}
    return {d["id"]: d for d in json.loads(path.read_text()).get("deals", [])}


def merge(candidates: list[Candidate], verifications: list[Verification], now: str) -> list[PublishedDeal]:
    previous = _load_previous()
    by_id = {c.id: c for c in candidates}
    deals: list[PublishedDeal] = []
    for v in verifications:
        c = by_id.get(v.id)
        if c is None or v.verdict != "verified" or v.confidence < MIN_CONFIDENCE:
            continue
        price = v.confirmed_price or c.current_price
        regular = v.confirmed_regular_price or c.regular_price
        if regular <= 0 or price >= regular:
            continue
        deals.append(PublishedDeal(
            id=c.id,
            title=c.title,
            retailer=c.retailer,
            category=c.category,
            deal_type=c.deal_type,
            url=c.url,
            image_url=v.image_url or c.image_url,
            price=round(price, 2),
            regular_price=round(regular, 2),
            discount_pct=round(100 * (1 - price / regular)),
            confidence=v.confidence,
            in_stock=v.in_stock,
            headline=c.title,
            notes=v.notes,
            first_seen=previous.get(c.id, {}).get("first_seen", now),
            last_verified=now,
        ))
    return deals


def run(candidates: list[Candidate], verifications: list[Verification], rejected_count: int) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    deals = merge(candidates, verifications, now)

    summary, featured = "No deals passed verification today. Check back tomorrow.", None
    if deals:
        report = run_agent(
            name="publisher",
            system=SYSTEM,
            prompt="Today's verified deals:\n\n" + json.dumps([d.model_dump() for d in deals], indent=2),
            output=PublisherReport,
            tools=[],
            effort="low",
        )
        headlines = {p.id: p.headline for p in report.picks}
        for d in deals:
            d.headline = headlines.get(d.id, d.headline)
        summary = report.summary
        featured = report.featured_id if any(d.id == report.featured_id for d in deals) else None

    featured = featured or (max(deals, key=lambda d: d.regular_price - d.price).id if deals else None)
    deals.sort(key=lambda d: (d.id != featured, d.deal_type != "price_error", -d.discount_pct))

    payload = {
        "updated_at": now,
        "summary": summary,
        "featured_id": featured,
        "stats": {
            "candidates": len(candidates),
            "verified": len(deals),
            "rejected": rejected_count,
        },
        "deals": [d.model_dump() for d in deals],
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "archive").mkdir(exist_ok=True)
    text = json.dumps(payload, indent=2)
    (DATA_DIR / "deals.json").write_text(text)
    (DATA_DIR / "archive" / f"{now[:10]}.json").write_text(text)
    return payload
