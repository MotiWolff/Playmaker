#!/usr/bin/env python3
"""
Non-interactive smoke test for Elasticsearch logging.

Usage examples:
  ELASTIC_HOST=http://localhost:9200 ELASTIC_LOG_INDEX=playmaker-logs \
  python scripts/test_es_logging.py --host http://localhost:9200 --index playmaker-logs
"""

import argparse
import os
import sys
import time
import uuid
from pathlib import Path

# Ensure repository root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.logging.logger import Logger

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover
    Elasticsearch = None  # type: ignore


def normalize_host(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description="ES logging smoke test")
    parser.add_argument(
        "--host",
        default=os.getenv("ELASTIC_HOST")
        or os.getenv("ELASTICSEARCH_HOST")
        or os.getenv("ELASTIC_URL")
        or "http://localhost:9200",
        help="Elasticsearch host URL",
    )
    parser.add_argument(
        "--index",
        default=os.getenv("ELASTIC_LOG_INDEX", "playmaker-logs"),
        help="Elasticsearch index name",
    )
    args = parser.parse_args()

    es_host = normalize_host(args.host)
    index = args.index

    unique_id = str(uuid.uuid4())
    message = f"es-log-smoke-test {unique_id}"

    # Emit a log via our logger (logger already uses ES-compatible headers)
    logger = Logger.get_logger()
    logger.info(message)

    # Allow a brief time for indexing
    time.sleep(2)

    if Elasticsearch is None:
        print("Elasticsearch client not installed. pip install elasticsearch")
        return 1

    print(f"Querying Elasticsearch host='{es_host}' index='{index}'")
    es = Elasticsearch([es_host])

    # Force ES 8-compatible headers on the search call
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }
    resp = es.options(headers=headers).search(
        index=index, query={"match_phrase": {"message": message}}
    )
    hits = resp.get("hits", {}).get("hits", [])
    if not hits:
        print("No log found in Elasticsearch. Check index and host.")
        print(f"Searched index='{index}' host='{es_host}' message='{message}'")
        return 2

    doc = hits[0]["_source"]
    print("Found log in Elasticsearch:")
    print({k: doc.get(k) for k in ["timestamp", "level", "logger", "message"]})
    print(f"Index: {index}")
    print(
        f"Peers can connect using host '{es_host}' and index '{index}'."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())