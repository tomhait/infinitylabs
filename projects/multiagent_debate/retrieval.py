"""Retrieval-backed academic search (Semantic Scholar + OpenAlex fallback)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

CACHE_DIR = ROOT / "outputs" / "retrieval_cache"
S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_SEARCH = "https://api.openalex.org/works"
FIELDS = (
    "title,abstract,year,venue,url,externalIds,publicationTypes,"
    "publicationVenue,journal"
)

_JOURNAL_TYPES = {
    "journalarticle",
    "review",
    "conference",
    "conferencepaper",
}
_PREPRINT_HINTS = ("arxiv", "biorxiv", "medrxiv", "preprint", "ssrn")


@dataclass
class Source:
    paper_id: str
    title: str
    abstract: str = ""
    year: int | None = None
    venue: str = ""
    url: str = ""
    doi: str | None = None
    publication_types: list[str] = field(default_factory=list)
    is_peer_reviewed: bool = False
    provider: str = "semanticscholar"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})


def _env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _classify_peer_reviewed(
    publication_types: list[str],
    venue: str,
    doi: str | None,
) -> bool:
    types_l = {t.lower().replace(" ", "") for t in publication_types}
    venue_l = (venue or "").lower()
    if any(h in venue_l for h in _PREPRINT_HINTS):
        return False
    if types_l & _JOURNAL_TYPES:
        return True
    if doi and venue_l and not any(h in venue_l for h in _PREPRINT_HINTS):
        return True
    return False


def _http_get_json(url: str, headers: dict[str, str], *, retries: int = 4) -> dict:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_err = exc
            # Honor Retry-After when present; otherwise exponential backoff
            if exc.code in (429, 500, 502, 503):
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                time.sleep(min(delay, 20))
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"HTTP failed after retries: {last_err}")


def _paper_from_s2(raw: dict) -> Source | None:
    title = (raw.get("title") or "").strip()
    if not title:
        return None
    external = raw.get("externalIds") or {}
    doi = external.get("DOI")
    venue = ""
    if raw.get("venue"):
        venue = str(raw["venue"])
    elif raw.get("journal") and isinstance(raw["journal"], dict):
        venue = str(raw["journal"].get("name") or "")
    elif raw.get("publicationVenue") and isinstance(raw["publicationVenue"], dict):
        venue = str(raw["publicationVenue"].get("name") or "")

    types = list(raw.get("publicationTypes") or [])
    url = (raw.get("url") or "").strip()
    if not url and doi:
        url = f"https://doi.org/{doi}"

    return Source(
        paper_id=str(raw.get("paperId") or ""),
        title=title,
        abstract=(raw.get("abstract") or "").strip(),
        year=raw.get("year"),
        venue=venue,
        url=url,
        doi=doi,
        publication_types=types,
        is_peer_reviewed=_classify_peer_reviewed(types, venue, doi),
        provider="semanticscholar",
    )


def _paper_from_openalex(raw: dict) -> Source | None:
    title = (raw.get("title") or raw.get("display_name") or "").strip()
    if not title:
        return None
    abstract = ""
    inverted = raw.get("abstract_inverted_index")
    if isinstance(inverted, dict) and inverted:
        # Reconstruct abstract from inverted index
        positions: list[tuple[int, str]] = []
        for word, idxs in inverted.items():
            for i in idxs:
                positions.append((i, word))
        abstract = " ".join(w for _, w in sorted(positions))

    doi = None
    doi_url = raw.get("doi") or ""
    if isinstance(doi_url, str) and "doi.org/" in doi_url:
        doi = doi_url.split("doi.org/", 1)[1]
    elif isinstance(doi_url, str) and doi_url.startswith("10."):
        doi = doi_url

    primary = raw.get("primary_location") or {}
    source = primary.get("source") or {}
    venue = str(source.get("display_name") or "")
    is_oa_journal = bool(source.get("type") == "journal")
    types = ["JournalArticle"] if is_oa_journal else []
    url = primary.get("landing_page_url") or raw.get("id") or ""
    if not url and doi:
        url = f"https://doi.org/{doi}"

    year = raw.get("publication_year")
    return Source(
        paper_id=str(raw.get("id") or title),
        title=title,
        abstract=abstract.strip(),
        year=int(year) if year else None,
        venue=venue,
        url=str(url),
        doi=doi,
        publication_types=types,
        is_peer_reviewed=_classify_peer_reviewed(types, venue, doi),
        provider="openalex",
    )


def build_search_queries(question: str) -> list[str]:
    base = re.sub(r"[?!.]", "", question).strip()
    return [
        "large language model alignment safety RLHF",
        "LLM jailbreak red teaming alignment evaluation",
        "frontier language models deployment safety",
        base,
    ]


def search_semantic_scholar(query: str, *, limit: int = 8, year_min: int = 2019) -> list[Source]:
    params = urllib.parse.urlencode(
        {
            "query": query,
            "limit": str(limit),
            "fields": FIELDS,
            "year": f"{year_min}-",
        }
    )
    headers = {
        "Accept": "application/json",
        "User-Agent": "multiagent-debate-mvp/0.1 (research)",
    }
    api_key = _env("semanticscholar_api_key", "SEMANTIC_SCHOLAR_API_KEY", "S2_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    payload = _http_get_json(f"{S2_SEARCH}?{params}", headers)
    sources: list[Source] = []
    for item in payload.get("data") or []:
        paper = _paper_from_s2(item)
        if paper and paper.abstract:
            sources.append(paper)
    return sources


def search_openalex(query: str, *, limit: int = 8, year_min: int = 2019) -> list[Source]:
    # mailto makes OpenAlex more tolerant of traffic
    mail = _env("openalex_mailto", "OPENALEX_MAILTO", "EMAIL") or "debate-mvp@example.com"
    params = urllib.parse.urlencode(
        {
            "search": query,
            "per_page": str(limit),
            "filter": f"from_publication_date:{year_min}-01-01,has_abstract:true",
            "mailto": mail,
        }
    )
    headers = {
        "Accept": "application/json",
        "User-Agent": f"multiagent-debate-mvp/0.1 (mailto:{mail})",
    }
    payload = _http_get_json(f"{OPENALEX_SEARCH}?{params}", headers)
    sources: list[Source] = []
    for item in payload.get("results") or []:
        paper = _paper_from_openalex(item)
        if paper and paper.abstract:
            sources.append(paper)
    return sources


def _cache_path(question: str) -> Path:
    digest = hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"sources_{digest}.json"


def _load_cache(question: str) -> list[Source] | None:
    path = _cache_path(question)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Source.from_dict(x) for x in data]


def _save_cache(question: str, sources: list[Source]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(question)
    path.write_text(
        json.dumps([s.to_dict() for s in sources], indent=2),
        encoding="utf-8",
    )


def retrieve_sources(
    question: str,
    *,
    max_sources: int = 8,
    use_cache: bool = True,
) -> list[Source]:
    if use_cache:
        cached = _load_cache(question)
        if cached:
            print(f"   using cached retrieval ({len(cached)} sources)")
            return cached[:max_sources]

    seen: set[str] = set()
    collected: list[Source] = []

    def _add(batch: list[Source]) -> None:
        for src in batch:
            key = (src.doi or src.paper_id or src.title).lower()
            if key in seen:
                continue
            seen.add(key)
            collected.append(src)

    # Primary: Semantic Scholar
    for query in build_search_queries(question):
        try:
            _add(search_semantic_scholar(query, limit=6))
            time.sleep(1.2)  # be polite to free tier
        except Exception as exc:  # noqa: BLE001
            print(f"   Semantic Scholar warning: {exc}")
        if len(collected) >= max_sources:
            break

    # Fallback: OpenAlex if S2 under-delivered
    if len(collected) < 3:
        print("   falling back to OpenAlex…")
        for query in build_search_queries(question)[:3]:
            try:
                _add(search_openalex(query, limit=6))
            except Exception as exc:  # noqa: BLE001
                print(f"   OpenAlex warning: {exc}")
            if len(collected) >= max_sources:
                break

    collected.sort(
        key=lambda s: (not s.is_peer_reviewed, -(s.year or 0), len(s.abstract) < 80)
    )
    result = collected[:max_sources]
    if result:
        _save_cache(question, result)
    return result


def format_sources_for_prompt(sources: list[Source]) -> str:
    blocks = []
    for i, s in enumerate(sources, 1):
        abstract = s.abstract[:1200] + ("…" if len(s.abstract) > 1200 else "")
        blocks.append(
            f"[{i}] {s.title} ({s.year or 'n.d.'})\n"
            f"Venue: {s.venue or 'unknown'} | peer_reviewed={s.is_peer_reviewed} | via={s.provider}\n"
            f"DOI: {s.doi or 'none'} | URL: {s.url or 'none'}\n"
            f"Abstract: {abstract}"
        )
    return "\n\n".join(blocks)
