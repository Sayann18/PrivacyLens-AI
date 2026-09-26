from __future__ import annotations

import re
from models.analysis_v2 import DocumentSection
from models.normalized_document import NormalizedDocument


class Sectionizer:
    TOPICS = {
        "data_collection": ["information collected", "information we collect", "data we collect", "personal information", "personal data"],
        "data_sharing": ["information sharing", "third parties", "service providers", "disclosure"],
        "tracking": ["cookies", "tracking", "analytics", "web beacons"],
        "billing": ["billing", "payment", "fees", "charges", "pricing"],
        "cancellation": ["cancellation", "cancel", "termination by you"],
        "refunds": ["refund", "reimbursement", "money back"],
        "liability": ["limitation of liability", "disclaimer", "liability"],
        "arbitration": ["arbitration", "dispute resolution", "class action"],
        "termination": ["termination", "suspension", "account suspension"],
        "governing_law": ["governing law", "jurisdiction", "venue"],
        "changes": ["changes to these terms", "changes to this policy", "updates to this policy"],
    }

    def sectionize(self, document: NormalizedDocument) -> list[DocumentSection]:
        source = document.raw_text
        lines = [line.strip() for line in source.splitlines()]
        heading_indices: list[tuple[int, str, str | None]] = []
        known = {phrase for values in self.TOPICS.values() for phrase in values}
        for i, line in enumerate(lines):
            normalized = re.sub(r"^[\d\s.)-]+", "", line.lower().rstrip(":")).strip()
            if not normalized or len(line) > 120:
                continue
            if normalized in known or any(normalized.startswith(k) for k in known):
                topic = next((topic for topic, vals in self.TOPICS.items() if any(normalized.startswith(v) for v in vals)), None)
                heading_indices.append((i, line[:120], topic))
        if not heading_indices:
            if document.pages:
                return [DocumentSection(section_id=f"section-{p.page_number}", title=f"Page {p.page_number}", text=p.text, page=p.page_number, section_type=None) for p in document.pages if p.text.strip()]
            return [DocumentSection(section_id="section-1", title="Document", text=source, page=None)] if source else []
        sections: list[DocumentSection] = []
        for pos, (start, title, topic) in enumerate(heading_indices):
            end = heading_indices[pos + 1][0] if pos + 1 < len(heading_indices) else len(lines)
            text = "\n".join(lines[start:end]).strip()
            page = None
            if document.pages:
                cumulative = 0
                for p in document.pages:
                    cumulative += len(p.text.splitlines())
                    if start < cumulative:
                        page = p.page_number
                        break
            sections.append(DocumentSection(section_id=f"section-{pos+1}", title=title, text=text, page=page, section_type=topic))
        return sections[:100]
