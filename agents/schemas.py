"""Data shapes passed between the three agents and the site."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Retailer = Literal["Amazon", "Costco", "Best Buy"]
Category = Literal["Laptop", "Tablet", "Phone", "Monitor", "TV", "Headphones", "Camera", "Gaming", "Smart Home", "Other"]
DealType = Literal["price_error", "flash_sale", "clearance", "major_discount"]
Verdict = Literal["verified", "rejected", "uncertain"]


class Candidate(BaseModel):
    """A deal the scout found and thinks is worth checking."""

    id: str = Field(description="Short slug, e.g. 'bestbuy-macbook-air-m4-13'")
    title: str
    retailer: Retailer
    category: Category
    deal_type: DealType
    url: str = Field(description="Direct product page URL at the retailer")
    image_url: str = Field(description="Direct URL to the retailer's product image, or empty string if not found")
    current_price: float
    regular_price: float = Field(description="Typical/list price the discount is measured against")
    evidence: str = Field(description="Where the price was seen and why it looks unusual")


class ScoutReport(BaseModel):
    candidates: list[Candidate]


class Verification(BaseModel):
    """The verifier's ruling on one scout candidate."""

    id: str = Field(description="Must match the candidate id")
    verdict: Verdict
    confirmed_price: float | None = Field(description="Price the verifier saw on the live page, or null if it could not see one")
    confirmed_regular_price: float | None
    in_stock: bool | None
    image_url: str = Field(description="Best product image URL found (may correct the scout's), or empty string")
    confidence: int = Field(ge=0, le=100)
    notes: str = Field(description="One or two sentences a shopper would find useful, e.g. 'Ships 10/24, limit 2 per order'")


class VerifierReport(BaseModel):
    verifications: list[Verification]


class PublishedDeal(BaseModel):
    """One card on the site."""

    id: str
    title: str
    retailer: Retailer
    category: Category
    deal_type: DealType
    url: str
    image_url: str
    price: float
    regular_price: float
    discount_pct: int
    confidence: int
    in_stock: bool | None
    headline: str
    notes: str
    first_seen: str
    last_verified: str


class EditorialPick(BaseModel):
    id: str
    headline: str = Field(description="Punchy one-line card headline, under 70 characters, no emoji")


class PublisherReport(BaseModel):
    summary: str = Field(description="Two-sentence overview of today's deals for the top of the site")
    featured_id: str = Field(description="id of the single best deal to feature at the top")
    picks: list[EditorialPick]
