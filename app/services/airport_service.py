import json
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "airports.json"
_airports: list[dict] | None = None
_codes: set[str] | None = None


def _load():
    global _airports, _codes
    if _airports is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _airports = json.load(f)
        _codes = {a["code"] for a in _airports}


def get_all_airports() -> list[dict]:
    """Retorna lista completa de aeroportos."""
    _load()
    return _airports


def is_valid_code(code: str) -> bool:
    """Verifica se o codigo IATA existe na base."""
    _load()
    return code.upper() in _codes


def search_airports(query: str, limit: int = 10) -> list[dict]:
    """Busca aeroportos por codigo, cidade ou nome."""
    _load()
    q = query.lower()
    results = []
    for a in _airports:
        if (q in a["code"].lower()
            or q in a["city"].lower()
            or q in a["name"].lower()
            or q in a["country"].lower()):
            results.append(a)
            if len(results) >= limit:
                break
    return results
