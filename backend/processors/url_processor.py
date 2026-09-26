from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

_BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal"}


@dataclass
class UrlExtractionResult:
    source: str
    final_url: str
    content_kind: str  
    text: str
    character_count: int
    warnings: list[str]


def is_ip_allowed(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return False
    if str(ip) == "169.254.169.254":  
        return False
    return True


def resolve_and_validate(hostname: str) -> str:
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError("This host is not allowed")
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError("Could not resolve hostname") from exc
    for result in addrinfo:
        ip = result[4][0]
        if is_ip_allowed(ip):
            return ip
    raise ValueError("This host resolves to a blocked network range")


def _pinned_request(client: httpx.AsyncClient, url: str, hostname: str, ip: str, headers: dict) -> httpx.Request:
    parsed = urlparse(url)
    netloc = f"[{ip}]" if ":" in ip else ip
    if parsed.port:
        netloc += f":{parsed.port}"
    pinned_url = parsed._replace(netloc=netloc).geturl()
    request = client.build_request("GET", pinned_url, headers={**headers, "Host": hostname})
    request.extensions["sni_hostname"] = hostname
    return request


async def _fetch_with_ssrf_protection(url: str, max_bytes: int) -> tuple[httpx.Response, str, bytes]:
    settings = get_settings()
    headers = {"User-Agent": "PrivacyLensAI/1.0"}
    current_url = url

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=False) as client:
        for _ in range(6):  
            parsed = urlparse(current_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("A public http(s) URL is required")

            ip = resolve_and_validate(parsed.hostname)
            request = _pinned_request(client, current_url, parsed.hostname, ip, headers)

            async with client.stream("GET", request.url, headers=request.headers, extensions=request.extensions) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirect without location")
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > max_bytes:
                    raise ValueError("The response is too large to process")

                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        raise ValueError("The response is too large to process")

                return response, current_url, bytes(body)
        raise ValueError("Too many redirects")


def _classify_content_type(content_type: str, body: bytes) -> str:
    content_type = content_type.lower()
    if "pdf" in content_type or body[:5] == b"%PDF-":
        return "pdf"
    if content_type.startswith("image/") or body[:3] == b"\xff\xd8\xff" or body[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    if "html" in content_type or "text" in content_type:
        return "html"
    return "unsupported"


async def extract_url(url: str, max_chars: int) -> UrlExtractionResult:
    settings = get_settings()
    response, final_url, body = await _fetch_with_ssrf_protection(url, settings.max_url_response_bytes)

    kind = _classify_content_type(response.headers.get("content-type", ""), body)
    warnings: list[str] = []

    if kind == "html":
        soup = BeautifulSoup(body.decode(response.encoding or "utf-8", errors="replace"), "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        text = " ".join(soup.stripped_strings)[:max_chars]
        return UrlExtractionResult(url, final_url, "html", text, len(text), warnings)

    if kind in ("pdf", "image"):
        from processors.extraction import extract_bytes_async

        filename = "downloaded.pdf" if kind == "pdf" else "downloaded.png"
        result = await extract_bytes_async(filename, body)
        if not result.success:
            raise ValueError(result.error or f"The linked {kind.upper()} could not be processed.")
        warnings.extend(result.warnings)
        text = result.text[:max_chars]
        return UrlExtractionResult(url, final_url, kind, text, len(text), warnings)

    raise ValueError("The URL returned an unsupported content type.")



async def extract_url_text(url: str, max_chars: int) -> str:
    return (await extract_url(url, max_chars)).text
