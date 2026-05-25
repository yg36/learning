from datetime import datetime
from datetime import timezone
from uuid import uuid4

from schemas import UIResponse


class UIResponseBuilder:
    """Create the UI-only JSON contract sent to frontend teammates."""

    SCHEMA_VERSION = "1.0"

    def build(self, recommendation_payload, request_id=None):
        profile = recommendation_payload.get("profile", {})
        components = recommendation_payload.get("components", [])

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "response_type": "ui_components",
            "request_id": request_id or f"rec_{uuid4().hex[:12]}",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "query": {
                "raw": profile.get("query", ""),
                "normalized": profile.get("normalized_query"),
                "intent": profile.get("intent"),
                "language": profile.get("query_language"),
            },
            "detected_context": {
                "skin_type": profile.get("skin_type"),
                "user_age": profile.get("user_age"),
                "age_group": profile.get("age_group"),
                "product_type": profile.get("product_type"),
                "skin_concerns": profile.get("skin_concerns", []),
                "requested_ingredients": profile.get("requested_ingredients", []),
                "avoided_ingredients": profile.get("avoided_ingredients", []),
                "safety_flags": {
                    "pregnancy_safe_required": bool(profile.get("pregnancy_safe_required")),
                    "vegan_preference": bool(profile.get("vegan_preference")),
                    "cruelty_free_preference": bool(profile.get("cruelty_free_preference")),
                },
            },
            "summary": {
                "component_count": len(components),
                "primary_component_id": components[0].get("component_id") if components else None,
                "safety_severity": self._safety_severity(components),
            },
            "components": components,
        }
        return UIResponse.model_validate(payload).model_dump(mode="json")

    def _safety_severity(self, components):
        for component in components:
            if component.get("component_type") == "safety_banner":
                return component.get("severity", "info")
        return None
