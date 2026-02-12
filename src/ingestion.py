from Bio import Entrez
import json
import os
import time
import logging

logger = logging.getLogger(__name__)

CACHE_PATH = "data/raw/pubmed_cache.json"
Entrez.email = os.getenv("ENTREZ_EMAIL")
Entrez.api_key = os.getenv("ENTREZ_API_KEY")


def fetch_pubmed_with_cache(query: str, max_results: int = 50, force_refresh: bool = False) -> list[dict]:
    """
    Fetch PubMed abstracts with caching support.

    Args:
        query: PubMed search query
        max_results: Maximum number of results to fetch
        force_refresh: Force refresh cache even if it exists

    Returns:
        List of dicts with 'pmid' and 'text' keys
    """
    if os.path.exists(CACHE_PATH) and not force_refresh:
        try:
            with open(CACHE_PATH) as f:
                cached = json.load(f)

            # Handle old cache format (list) vs new format (dict)
            if isinstance(cached, list):
                logger.warning("Old cache format detected (list). Rebuilding cache with new format.")
            elif isinstance(cached, dict):
                # Check if query matches
                if cached.get("query") == query and cached.get("max_results", max_results) == max_results:
                    logger.info(f"Using cached PubMed data for query: '{query}'")
                    return cached["data"]
                else:
                    logger.info(f"Cache query mismatch. Cached: '{cached.get('query')}', Requested: '{query}'")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid cache file, rebuilding: {e}")

    # Fetch fresh data
    logger.info(f"Fetching PubMed abstracts for query: '{query}' (max_results={max_results})")
    abstracts = fetch_pubmed(query, max_results)

    # Save to cache
    os.makedirs("data/raw", exist_ok=True)

    cache_data = {
        "query": query,
        "max_results": max_results,
        "timestamp": time.time(),
        "data": abstracts
    }

    with open(CACHE_PATH, "w") as f:
        json.dump(cache_data, f, indent=2)

    logger.info(f"Cached {len(abstracts)} abstracts to {CACHE_PATH}")
    return abstracts


def fetch_pubmed(query: str, max_results: int = 50) -> list[dict]:
    """
    Fetch abstracts from PubMed via Entrez API.

    Args:
        query: PubMed search query
        max_results: Maximum number of results

    Returns:
        List of dicts with 'pmid' and 'text' keys
    """
    try:
        # Search for PMIDs
        logger.info(f"Searching PubMed: '{query}'")
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        ids = record["IdList"]

        if not ids:
            logger.warning(f"No results found for query: '{query}'")
            return []

        logger.info(f"Found {len(ids)} PMIDs, fetching abstracts...")

        abstracts = []

        for i, pmid in enumerate(ids, 1):
            try:
                fetch = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text")
                text = fetch.read()
                abstracts.append({
                    "pmid": pmid,
                    "text": text
                })

                if i % 10 == 0:
                    logger.info(f"Fetched {i}/{len(ids)} abstracts")

                # Rate limiting: NCBI recommends 3 requests/second without API key, 10/second with key
                # Sleep for 0.34s = ~3 requests/second (conservative)
                time.sleep(0.34)

            except Exception as e:
                logger.error(f"Failed to fetch PMID {pmid}: {e}")
                continue

        logger.info(f"Successfully fetched {len(abstracts)} abstracts")
        return abstracts

    except Exception as e:
        logger.error(f"PubMed fetch failed: {e}")
        raise
