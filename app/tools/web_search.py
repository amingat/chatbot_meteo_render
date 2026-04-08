import requests
from duckduckgo_search import DDGS
from langchain_core.tools import tool

from app.config import get_settings


def _tavily_search(query: str, api_key: str) -> list[dict]:
    response = requests.post(
        'https://api.tavily.com/search',
        json={
            'api_key': api_key,
            'query': query,
            'search_depth': 'advanced',
            'max_results': 5,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get('results', [])


def _duckduckgo_search(query: str) -> list[dict]:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    normalized = []
    for item in results:
        normalized.append(
            {
                'title': item.get('title'),
                'url': item.get('href'),
                'content': item.get('body'),
            }
        )
    return normalized


@tool
def web_search_tool(query: str) -> str:
    """Recherche des informations récentes sur le web."""
    settings = get_settings()
    try:
        if settings.tavily_api_key:
            results = _tavily_search(query, settings.tavily_api_key)
        else:
            results = _duckduckgo_search(query)

        if not results:
            return 'Aucun résultat trouvé sur le web.'

        lines = []
        for idx, item in enumerate(results, start=1):
            title = item.get('title') or 'Sans titre'
            url = item.get('url') or item.get('href') or ''
            snippet = item.get('content') or item.get('body') or ''
            lines.append(f"{idx}. {title}\nURL: {url}\nRésumé: {snippet}")
        return 'Résultats web externes:\n\n' + '\n\n'.join(lines)
    except Exception as exc:
        return f'Erreur de recherche web: {exc}'
