# UI Response Contract

This file describes the JSON that should be shared with the UI team.

Use `ui_response.json` or files under `samples/`. Do not use full `output.json`
for UI integration unless the frontend needs backend debugging fields.

## Top-Level Shape

```json
{
  "schema_version": "1.0",
  "response_type": "ui_components",
  "request_id": "rec_abc123",
  "generated_at": "2026-05-22T00:00:00+00:00",
  "query": {},
  "detected_context": {},
  "summary": {},
  "components": []
}
```

## Component Types

Supported `component_type` values:

| Type | UI Use |
|---|---|
| `safety_banner` | Full-width safety or caution message |
| `hero_product_carousel` | Primary best-match product cards |
| `personalized_product_carousel` | History-based recommendations |
| `product_carousel` | Standard product catalog row |
| `routine_product_carousel` | Products for next routine step |
| `budget_product_carousel` | Budget-focused product row |
| `routine_timeline` | Morning and night routine lanes |
| `comparison_table` | Compare top products |
| `empty_state` | Fallback when nothing strong is available |

## Product Card Fields

Every card in a carousel includes:

| Field | Meaning |
|---|---|
| `card_id` | Stable frontend key |
| `card_variant` | Rendering style such as `product_card`, `history_match_card`, `routine_step_card`, `safety_product_card`, `budget_card` |
| `rank` | Position inside the component |
| `title` | Product title |
| `subtitle` | Brand and product type |
| `price` | Numeric price |
| `rating` | Numeric rating |
| `primary_tags` | Short tags to show on card |
| `badges` | Display badges |
| `display` | UI-ready text strings |
| `explanation` | Reason and confidence |
| `actions` | UI actions to render |
| `analytics` | IDs and event names for tracking |

## Display Object

The frontend should prefer `display` text over constructing copy itself.

```json
{
  "display": {
    "title": "Retinol Renewal Night Serum",
    "subtitle": "Olay - Serum",
    "price_text": "INR 1450",
    "rating_text": "4.8 rating",
    "reason_text": "Directly matches the product intent detected from your query.",
    "badge_text": "Night use / Top rated"
  }
}
```

## Render Hints

`render_hints` are suggestions, not strict frontend rules.

Common fields:

| Field | Meaning |
|---|---|
| `desktop_layout` | Preferred desktop card/layout |
| `mobile_layout` | Preferred mobile card/layout |
| `max_visible_cards` | Suggested visible cards before scrolling |
| `show_badges` | Whether badges should be displayed |
| `show_reason` | Whether reason text should be displayed |

## Analytics

Cards include:

```json
{
  "analytics": {
    "catalog_id": "query_match",
    "slot_id": "query_match_1",
    "rank": 1,
    "product_id": "prod_001",
    "events": ["impression", "click", "save", "add_to_routine"]
  }
}
```

The UI team can attach these values to their own event logger.

## Files For UI Team

| File | Purpose |
|---|---|
| `ui_response.json` | Latest UI-only output from `main.py` |
| `ui_response.schema.json` | JSON Schema for validation |
| `samples/retinol_query_ui_response.json` | Retinol safety and routine example |
| `samples/sunscreen_query_ui_response.json` | Sunscreen catalog example |
| `samples/pregnancy_safe_ui_response.json` | Pregnancy-safe safety filtering example |
| `samples/no_result_ui_response.json` | Empty-state example |

## Regenerate Artifacts

```powershell
venv\Scripts\python.exe generate_ui_artifacts.py
```
