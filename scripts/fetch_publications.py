"""
fetch_publications.py
─────────────────────
Fetches publications from ORCID and Semantic Scholar (both free, no API key needed),
merges and deduplicates them, and writes data/publications.json.

Run manually:   python scripts/fetch_publications.py
Run via GitHub Actions automatically every night.

Requirements:   pip install requests
"""

import json
import time
import requests
from datetime import date
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
# Add each researcher's ORCID ID here (https://orcid.org to get yours free)
ORCID_IDS = [
    "0000-0002-3991-5537",   # Dr. Muntasir Alam
    "0009-0003-6685-835X",   # Nuruzzaman Rahat
]

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "publications.json"
# ──────────────────────────────────────────────────────────────────────────────


def fetch_orcid(orcid_id: str) -> list[dict]:
    """Fetch works from the ORCID public API (no auth needed for public profiles)."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {"Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ORCID fetch failed for {orcid_id}: {e}")
        return []

    pubs = []
    for group in (data.get("group") or []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        s = summaries[0]  # take the preferred/first summary

        title = (s.get("title", {}) or {}).get("title", {}).get("value", "").strip()
        if not title:
            continue

        year = None
        pub_date = s.get("publication-date") or {}
        if pub_date.get("year"):
            try:
                year = int(pub_date["year"]["value"])
            except (TypeError, ValueError):
                pass

        doi = None
        for ext_id in (group.get("external-ids", {}) or {}).get("external-id", []):
            if ext_id.get("external-id-type") == "doi":
                doi = ext_id.get("external-id-value", "").strip().lower()
                doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
                break

        pub_type = s.get("type", "").lower()
        mapped_type = "conference" if "proceedings" in pub_type or "conference" in pub_type else "journal"

        venue = (s.get("journal-title") or {}).get("value", "") or ""

        pubs.append({
            "title":   title,
            "year":    year,
            "doi":     doi,
            "type":    mapped_type,
            "venue":   venue,
            "authors": [],   # enriched later via Semantic Scholar
            "tags":    [],
            "citations": 0,
            "abstract":  "",
            "url":     f"https://doi.org/{doi}" if doi else "",
        })

    print(f"  ORCID {orcid_id}: found {len(pubs)} works")
    return pubs


def enrich_via_semantic_scholar(pubs: list[dict]) -> list[dict]:
    """
    For publications that have a DOI, look them up on Semantic Scholar
    to add: authors, citation count, abstract, venue correction.
    Free API — no key required. Polite rate: 1 req / sec.
    """
    enriched = []
    for pub in pubs:
        if not pub.get("doi"):
            enriched.append(pub)
            continue

        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{pub['doi']}"
        params = {"fields": "title,authors,year,citationCount,abstract,venue,publicationTypes"}
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                d = r.json()
                pub["authors"]   = [a["name"] for a in (d.get("authors") or [])]
                pub["citations"] = d.get("citationCount") or 0
                pub["abstract"]  = d.get("abstract") or pub["abstract"]
                if d.get("venue"):
                    pub["venue"] = d["venue"]
                # Refine type
                ptypes = [t.lower() for t in (d.get("publicationTypes") or [])]
                if "conference" in ptypes:
                    pub["type"] = "conference"
                elif "journalarticle" in ptypes:
                    pub["type"] = "journal"
            elif r.status_code == 404:
                pass  # not in Semantic Scholar — keep ORCID data
            else:
                print(f"  SemanticScholar {pub['doi']}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  SemanticScholar error for {pub['doi']}: {e}")

        enriched.append(pub)
        time.sleep(1.1)   # polite rate limit: ~1 req/sec

    return enriched


def fetch_by_author_name(name: str) -> list[dict]:
    """
    Fallback: search Semantic Scholar by author name if someone has no ORCID.
    Returns their recent papers (last 50).
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": name,
        "fields": "title,authors,year,citationCount,abstract,venue,publicationTypes,externalIds",
        "limit": 50,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        papers = r.json().get("data", [])
    except Exception as e:
        print(f"  Author search failed for {name}: {e}")
        return []

    results = []
    for p in papers:
        doi = (p.get("externalIds") or {}).get("DOI", "")
        ptypes = [t.lower() for t in (p.get("publicationTypes") or [])]
        results.append({
            "title":     p.get("title", ""),
            "year":      p.get("year"),
            "doi":       doi.lower() if doi else "",
            "type":      "conference" if "conference" in ptypes else "journal",
            "venue":     p.get("venue", ""),
            "authors":   [a["name"] for a in (p.get("authors") or [])],
            "citations": p.get("citationCount") or 0,
            "abstract":  p.get("abstract") or "",
            "url":       f"https://doi.org/{doi}" if doi else "",
            "tags":      [],
        })
    return results


def deduplicate(pubs: list[dict]) -> list[dict]:
    """Remove duplicates by DOI (when present), then by normalised title."""
    seen_doi   = set()
    seen_title = set()
    out = []
    for p in sorted(pubs, key=lambda x: x.get("year") or 0, reverse=True):
        doi   = (p.get("doi") or "").strip().lower()
        title = " ".join(p.get("title", "").lower().split())
        if doi and doi in seen_doi:
            continue
        if title in seen_title:
            continue
        if doi:
            seen_doi.add(doi)
        seen_title.add(title)
        out.append(p)
    return out


def main():
    print("=== Fetching publications ===")
    all_pubs: list[dict] = []

    # 1. Fetch from ORCID
    for oid in ORCID_IDS:
        print(f"\nORCID: {oid}")
        pubs = fetch_orcid(oid)
        all_pubs.extend(pubs)
        time.sleep(0.5)

    # 2. Enrich with Semantic Scholar
    print(f"\nEnriching {len(all_pubs)} works via Semantic Scholar…")
    all_pubs = enrich_via_semantic_scholar(all_pubs)

    # 3. Deduplicate
    all_pubs = deduplicate(all_pubs)

    # 4. Sort newest first
    all_pubs.sort(key=lambda p: p.get("year") or 0, reverse=True)

    # 5. Write JSON
    output = {
        "last_updated": str(date.today()),
        "publications": all_pubs,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Wrote {len(all_pubs)} publications to {OUTPUT_FILE}")
    print(f"✓ Last updated: {output['last_updated']}")


if __name__ == "__main__":
    main()
