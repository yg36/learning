import json
from datetime import datetime
from pathlib import Path


DEFAULT_HISTORY_PATH = Path("data/user_history.json")
MAX_HISTORY_ITEMS = 30


def load_user_history(path=DEFAULT_HISTORY_PATH):
    path = Path(path)
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def merge_histories(base, incoming):
    merged = dict(base or {})
    for key, value in (incoming or {}).items():
        if isinstance(value, list):
            merged[key] = _dedupe(_as_list(merged.get(key)) + value)
        elif isinstance(value, dict):
            nested = dict(merged.get(key, {})) if isinstance(merged.get(key), dict) else {}
            nested.update(value)
            merged[key] = nested
        elif value not in (None, ""):
            merged[key] = value
    return merged


def save_user_history(history, path=DEFAULT_HISTORY_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=4, ensure_ascii=False), encoding="utf-8")
    return path


def update_user_history(history, query, profile, catalogs, path=DEFAULT_HISTORY_PATH):
    history = dict(history or {})
    top_products = _top_products(catalogs)
    now = datetime.now().isoformat(timespec="seconds")

    history["previous_queries"] = _prepend(history.get("previous_queries"), query)
    history["previous_clicked_product_titles"] = _prepend(
        history.get("previous_clicked_product_titles"),
        [product["title"] for product in top_products[:3]],
    )
    history["previous_clicked_tags"] = _prepend(
        history.get("previous_clicked_tags"),
        ["|".join(product.get("tags", [])[:8]) for product in top_products[:3]],
    )
    history["previous_hovered_product_titles"] = _prepend(
        history.get("previous_hovered_product_titles"),
        [product["title"] for product in top_products[1:5]],
    )
    history["previous_hovered_tags"] = _prepend(
        history.get("previous_hovered_tags"),
        ["|".join(product.get("tags", [])[:8]) for product in top_products[1:5]],
    )
    history["favorite_ingredients"] = _prepend(
        history.get("favorite_ingredients"),
        profile.get("requested_ingredients", []),
    )
    history["disliked_ingredients"] = _prepend(
        history.get("disliked_ingredients"),
        profile.get("avoided_ingredients", []),
    )
    history["last_profile"] = {
        "skin_type": profile.get("skin_type"),
        "skin_concerns": profile.get("skin_concerns", []),
        "product_type": profile.get("product_type"),
        "intent": profile.get("intent"),
        "updated_at": now,
    }
    history["updated_at"] = now

    save_user_history(history, path)
    return history


def _top_products(catalogs):
    products = []
    seen = set()
    for catalog in catalogs:
        for product in catalog.get("products", []):
            title = product.get("title")
            if not title or title in seen:
                continue
            products.append(product)
            seen.add(title)
    return products


def _prepend(existing, incoming):
    values = _as_list(incoming) + _as_list(existing)
    return _dedupe(values)[:MAX_HISTORY_ITEMS]


def _dedupe(values):
    result = []
    seen = set()
    for value in values:
        value = str(value).strip()
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
