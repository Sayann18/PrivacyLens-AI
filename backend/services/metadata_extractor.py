from __future__ import annotations

import re
from dataclasses import dataclass

from models.normalized_document import NormalizedDocument


@dataclass(frozen=True)
class MetadataResult:
    company: str | None = None
    product: str | None = None
    effective_date: str | None = None
    last_updated: str | None = None
    version: str | None = None
    jurisdiction: str | None = None


class DocumentMetadataExtractor:
    DATE = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}"

    def extract(self, document: NormalizedDocument) -> MetadataResult:
        text = document.raw_text
        company = None
        m = re.search(r"(?:provided|operated|owned|copyright)\s+by\s+([A-Z][A-Za-z0-9&.,' -]{1,100}?)(?:\.|,|\n)", text)
        if m:
            company = m.group(1).strip(" ,.")
        if not company:
            m = re.search(r"\b([A-Z][A-Za-z0-9&' -]{1,70}\s+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation))\b", text)
            if m:
                company = m.group(1).strip()
        product = None
        m = re.search(r"(?:for|service|product)\s+([A-Z][A-Za-z0-9 -]{2,60})", text)
        if m and "service" not in m.group(1).lower():
            product = m.group(1).strip(" .,")
        dates = re.findall(self.DATE, text, re.I)
        version = None
        m = re.search(r"\bversion\s*[:#]?\s*([0-9]+(?:\.[0-9]+){1,3})\b", text, re.I)
        if m:
            version = m.group(1)
        effective = None
        last_updated = None
        m = re.search(r"(?:effective|effective date)\s*[:\-]?\s*(%s)" % self.DATE, text, re.I)
        if m:
            effective = m.group(1)
        m = re.search(r"(?:last updated|updated on|updated)\s*[:\-]?\s*(%s)" % self.DATE, text, re.I)
        if m:
            last_updated = m.group(1)
        if not effective and dates:
            effective = dates[0]
        jurisdiction = None
        m = re.search(r"(?:laws? of|governed by the laws? of|jurisdiction of)\s+([A-Z][A-Za-z .'-]{2,80})", text, re.I)
        if m:
            jurisdiction = m.group(1).strip(" .,")
        return MetadataResult(company, product, effective, last_updated, version, jurisdiction)
