"""Adzuna API integration for job ingestion."""
import logging
from typing import List, Dict, Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def fetch_jobs(country: str = 'us', page: int = 1, results_per_page: int = 50) -> List[Dict[str, Any]]:
    cfg = settings.ADZUNA_CONFIG
    app_id = cfg.get('APP_ID')
    api_key = cfg.get('API_KEY')
    if not app_id or not api_key:
        logger.warning("Adzuna credentials not configured")
        return []

    url = f"{cfg['BASE_URL']}/{country}/search/{page}"
    params = {'app_id': app_id, 'app_key': api_key, 'results_per_page': results_per_page}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get('results', [])
    except Exception as e:
        logger.warning("Adzuna fetch failed: %s", e)
    return []
