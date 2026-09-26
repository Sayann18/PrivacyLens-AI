from __future__ import annotations

import re
from uuid import uuid4

from models.analysis_v2 import DocumentSection
from models.enums import ExtractionStatus
from models.normalized_document import NormalizedDocument, NormalizedPage
from processors.extraction import ExtractionResult
from processors.url_processor import UrlExtractionResult


class DocumentNormalizer:

    @staticmethod
    def _language(text: str) -> str:
        if not text.strip():
            return "unknown"
        latin = len(re.findall(r"[A-Za-z]", text))
        letters = len(re.findall(r"[A-Za-z\u00C0-\u024F\u0900-\u097F\u0980-\u09FF]", text))
        if letters and latin / letters > 0.75:
            return "en"
        return "mixed"

    @staticmethod
    def _status(result: ExtractionResult) -> ExtractionStatus:
        if result.success and result.text.strip():
            return ExtractionStatus.PARTIAL if result.partial else ExtractionStatus.COMPLETE
        if result.error_code in {"EMPTY_DOCUMENT", "EMPTY_FILE"} or result.status == "NO_ANALYZABLE_CONTENT":
            return ExtractionStatus.NO_READABLE_CONTENT
        return ExtractionStatus.FAILED

    @staticmethod
    def _sections_from_pages(pages: list[NormalizedPage]) -> list[DocumentSection]:
        if not pages:
            return []
        return [
            DocumentSection(
                section_id=f"section-{page.page_number}",
                title=f"Page {page.page_number}",
                text=page.text,
                page=page.page_number,
                section_type=None,
            )
            for page in pages
            if page.text.strip()
        ]

    def from_extraction_result(self, result: ExtractionResult) -> NormalizedDocument:
        pages = [
            NormalizedPage(
                page_number=p.page_number,
                text=p.text,
                extraction_method=p.extraction_method,
                ocr=p.ocr,
                warning=p.warning,
            )
            for p in result.pages
        ]
        if not pages and result.text.strip():
            pages = [NormalizedPage(page_number=1, text=result.text, extraction_method=result.extraction_method)]
        return NormalizedDocument(
            document_id=str(uuid4()),
            source_type="file",
            source_name=result.filename,
            detected_file_type=result.file_type,
            raw_text=result.text,
            pages=pages,
            sections=self._sections_from_pages(pages),
            language=self._language(result.text),
            character_count=len(result.text),
            extraction_method=result.extraction_method,
            extraction_confidence=result.confidence,
            extraction_status=self._status(result),
            partial=result.partial,
            warnings=list(result.warnings),
            metadata=dict(result.metadata),
        )

    def from_url_result(self, result: UrlExtractionResult) -> NormalizedDocument:
        page = NormalizedPage(page_number=1, text=result.text, extraction_method="url")
        return NormalizedDocument(
            document_id=str(uuid4()),
            source_type="url",
            source_name=result.final_url,
            source_url=result.final_url,
            detected_file_type=result.content_kind,
            raw_text=result.text,
            pages=[page] if result.text else [],
            sections=[DocumentSection(section_id="section-1", title="Document", text=result.text, page=1)] if result.text else [],
            language=self._language(result.text),
            character_count=len(result.text),
            extraction_method="url",
            extraction_confidence=1.0,
            extraction_status=ExtractionStatus.COMPLETE if result.text else ExtractionStatus.NO_READABLE_CONTENT,
            partial=False,
            warnings=list(result.warnings),
            metadata={"final_url": result.final_url, "content_kind": result.content_kind},
        )

    def from_text(self, text: str, source: str = "pasted text") -> NormalizedDocument:
        cleaned = text.strip()
        page = NormalizedPage(page_number=1, text=cleaned, extraction_method="text")
        return NormalizedDocument(
            document_id=str(uuid4()),
            source_type="text",
            source_name=source,
            detected_file_type="text",
            raw_text=cleaned,
            pages=[page] if cleaned else [],
            sections=[DocumentSection(section_id="section-1", title="Document", text=cleaned, page=1)] if cleaned else [],
            language=self._language(cleaned),
            character_count=len(cleaned),
            extraction_method="text",
            extraction_confidence=1.0,
            extraction_status=ExtractionStatus.COMPLETE if cleaned else ExtractionStatus.NO_READABLE_CONTENT,
        )
